"""API tests with a stubbed crew. No model calls."""

import json
import threading

from fastapi.testclient import TestClient

from backend.guardrails import render_markdown
from backend.runner import reset_executor, set_executor
from backend.store import get_store
from backend.trace import write_event


def _requisition(**overrides):
    body = {
        "title": "Ruby on Rails and React engineer",
        "description": "Build the product.",
        "responsibilities": "Ship features.",
        "requirements": "Ruby on Rails",
        "preferred_qualifications": "React",
        "perks_and_benefits": "Remote",
    }
    body.update(overrides)
    return body


def _draft(run_id: str) -> None:
    ranking = {
        "ordered_candidate_ids": ["c1"],
        "summary": "Ada matches the Rails requirement.",
        "rows": [
            {
                "candidate_id": "c1",
                "name": "Ada Lovelace",
                "source_type": "operator-supplied",
                "source_url": "",
                "score": 4,
                "met_requirements": ["Ruby on Rails"],
                "missing_requirements": ["React"],
            }
        ],
    }
    get_store().update(
        run_id,
        status="draft",
        candidates=[{"id": "c1", "name": "Ada Lovelace", "summary": "Pasted lead", "source_type": "operator-supplied", "source_url": "", "email": None, "phone": None}],
        evaluations=[{"candidate_id": "c1", "score": 4, "met_requirements": ["Ruby on Rails"], "missing_requirements": ["React"], "evidence_note": "Pasted lead names Rails."}],
        ranking=ranking,
        recommendation_markdown=render_markdown("Ruby on Rails and React engineer", ranking, "draft"),
        source_elapsed_ms=25,
        error=None,
    )


def test_f1_requires_title_and_requirements(client: TestClient):
    missing_title = client.post("/api/runs", json={"requisition": _requisition(title="  "), "pasted_leads": "Ada"})
    assert missing_title.status_code == 400
    assert missing_title.json()["error"]["message"] == "title is required."
    missing_requirements = client.post("/api/runs", json={"requisition": _requisition(requirements=""), "pasted_leads": "Ada"})
    assert missing_requirements.status_code == 400
    assert "requirements" in missing_requirements.json()["error"]["message"]


def test_one_active_run_then_f1_through_f5(client: TestClient):
    release = threading.Event()

    def executor(run_id: str) -> None:
        release.wait(5)
        _draft(run_id)

    set_executor(executor)
    first = client.post("/api/runs", json={"requisition": _requisition(), "pasted_leads": "Ada Lovelace, Rails engineer"})
    assert first.status_code == 202
    run_id = first.json()["run_id"]
    assert first.json()["status"] == "researching"
    second = client.post("/api/runs", json={"requisition": _requisition(), "pasted_leads": "Grace"})
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "run_in_progress"

    early_accept = client.post(f"/api/runs/{run_id}/accept", json={"recruiter_label": "Jamie"})
    assert early_accept.status_code == 409
    assert early_accept.json()["error"]["code"] == "invalid_state"
    hidden = client.get(f"/api/runs/{run_id}/recommendation")
    assert hidden.status_code == 404

    release.set()
    for _ in range(50):
        document = client.get(f"/api/runs/{run_id}").json()
        if document["status"] == "draft":
            break
    assert document["status"] == "draft"
    assert document["source_elapsed_ms"] == 25
    assert document["candidates"][0]["id"] == "c1"

    too_soon = client.post(f"/api/runs/not-a-uuid/satisfaction", json={"score": 4, "comment": ""})
    assert too_soon.status_code == 404
    bad_score = client.post(f"/api/runs/{run_id}/satisfaction", json={"score": "5", "comment": ""})
    assert bad_score.status_code == 400
    saved = client.post(f"/api/runs/{run_id}/satisfaction", json={"score": 5, "comment": "Useful shortlist"})
    assert saved.status_code == 200
    assert saved.json()["satisfaction"]["score"] == 5

    accepted = client.post(f"/api/runs/{run_id}/accept", json={"recruiter_label": "Jamie Recruiter"})
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert accepted.json()["recruiter_label"] == "Jamie Recruiter"
    assert accepted.json()["accepted_at"]
    shown = client.get(f"/api/runs/{run_id}/recommendation")
    assert shown.status_code == 200
    assert shown.json()["ranking"]["rows"][0]["source_type"] == "operator-supplied"
    assert "Contact decisions happen outside this product." in shown.json()["markdown"]
    reset_executor()


def test_discard_does_not_accept_and_failed_run_cannot_be_accepted(client: TestClient):
    set_executor(_draft)
    created = client.post("/api/runs", json={"requisition": _requisition(), "pasted_leads": "Ada"})
    run_id = created.json()["run_id"]
    for _ in range(50):
        if client.get(f"/api/runs/{run_id}").json()["status"] == "draft":
            break
    discarded = client.post(f"/api/runs/{run_id}/discard")
    assert discarded.status_code == 200
    assert discarded.json()["status"] == "discarded"
    assert discarded.json()["accepted_at"] is None
    assert client.get(f"/api/runs/{run_id}/recommendation").status_code == 404

    failed = get_store().create(_requisition(), "Grace")
    get_store().fail(failed["run_id"], "research", "model unavailable")
    rejected = client.post(f"/api/runs/{failed['run_id']}/accept", json={"recruiter_label": "Jamie"})
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "invalid_state"
    assert client.get(f"/api/runs/{failed['run_id']}").json()["status"] == "failed"
    early_score = client.post(f"/api/runs/{failed['run_id']}/satisfaction", json={"score": 3, "comment": ""})
    assert early_score.status_code == 409
    reset_executor()


def test_posting_text_does_not_create_a_run_and_blocks_private_urls(client: TestClient):
    preview = client.post(
        "/api/postings/preview",
        json={
            "text": "Staff Engineer\n\nRequirements\nPython\n\nResponsibilities\nLead the team\n"
        },
    )
    assert preview.status_code == 200
    assert preview.json()["requisition"]["title"] == "Staff Engineer"
    assert "Python" in preview.json()["requisition"]["requirements"]
    assert client.get("/api/runs/00000000-0000-0000-0000-000000000000").status_code == 404
    blocked = client.post("/api/postings/preview", json={"url": "http://example.com/job"})
    assert blocked.status_code == 502
    assert blocked.json()["error"]["code"] == "posting_fetch_failed"
    local = client.post("/api/postings/preview", json={"url": "https://127.0.0.1/job"})
    assert local.status_code == 502


def test_startup_marks_stale_run_failed(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKEND_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("BACKEND_LOG_DIR", str(tmp_path / "logs"))
    run_id = "11111111-1111-1111-1111-111111111111"
    directory = tmp_path / "runs" / run_id
    directory.mkdir(parents=True)
    (directory / "run.json").write_text(
        json.dumps({"run_id": run_id, "status": "researching", "candidates": None, "error": None}),
        encoding="utf-8",
    )
    from backend.store import reset_store

    reset_store()
    from backend.app import app

    with TestClient(app) as local_client:
        document = local_client.get(f"/api/runs/{run_id}").json()
    assert document["status"] == "failed"
    assert document["error"]["stage"] == "research"
    reset_store()


def test_pages_share_the_api_origin(client: TestClient):
    home = client.get("/")
    assert home.status_code == 200
    assert "text/html" in home.headers["content-type"]
    assert "/js/api.js" in home.text
    assert 'id="run"' in home.text
    manager = client.get("/hiring-manager")
    assert manager.status_code == 200
    assert "text/html" in manager.headers["content-type"]
    assert "/js/hiring-manager.js" in manager.text
    assert 'id="run"' not in manager.text
    assert 'id="accept"' not in manager.text
    assert 'id="discard"' not in manager.text
    script = client.get("/js/api.js")
    assert script.status_code == 200
    assert "/api/runs" in script.text
    assert "/api/postings/preview" in script.text
    assert client.get("/css/app.css").status_code == 200
    assert client.get("/health").json()["status"] == "ok"

    preview = client.post(
        "/api/postings/preview",
        json={"text": "Staff Engineer\n\nRequirements\nPython\n"},
    )
    assert preview.status_code == 200
    assert preview.json()["requisition"]["title"] == "Staff Engineer"

    set_executor(lambda run_id: get_store().fail(run_id, "research", "No pasted leads and search is off."))
    created = client.post(
        "/api/runs",
        json={"requisition": _requisition(title="Staff Engineer", requirements="Python"), "pasted_leads": ""},
    )
    assert created.status_code == 202
    run_id = created.json()["run_id"]
    for _ in range(50):
        document = client.get(f"/api/runs/{run_id}").json()
        if document["status"] != "researching":
            break
    assert document["status"] == "failed"
    assert document["error"]["stage"] == "research"
    assert client.get(f"/api/runs/{run_id}/recommendation").status_code == 404
    reset_executor()


def test_log_redacts_secret_values(monkeypatch, tmp_path):
    monkeypatch.setenv("BACKEND_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-testsecretvalue")
    write_event({"event": "task_start", "message": "key sk-testsecretvalue"})
    text = (tmp_path / "trace.jsonl").read_text(encoding="utf-8")
    assert "sk-testsecretvalue" not in text
    assert "[REDACTED]" in text
