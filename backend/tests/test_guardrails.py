"""Unit tests for task guardrails. No model calls."""

from backend.guardrails import (
    GuardrailError,
    canonical_order,
    render_markdown,
    validate_evaluations,
    validate_recommendation,
    validate_research,
)


def _candidate(candidate_id: str, name: str, source_type: str = "operator-supplied", source_url: str = "") -> dict:
    return {
        "id": candidate_id,
        "name": name,
        "summary": f"Notes about {name}",
        "source_type": source_type,
        "source_url": source_url,
        "email": None,
        "phone": None,
    }


def test_empty_research_without_leads_fails():
    try:
        validate_research({"candidates": []}, pasted_leads="", search_enabled=False)
    except GuardrailError as exc:
        assert "does not invent" in str(exc)
    else:
        raise AssertionError("empty research should fail")


def test_research_rejects_more_than_ten_and_web_without_url():
    too_many = {"candidates": [_candidate(f"c{i}", f"Person {i}") for i in range(11)]}
    try:
        validate_research(too_many, pasted_leads="leads", search_enabled=False)
        raise AssertionError("expected a length failure")
    except GuardrailError as exc:
        assert "maximum" in str(exc)
    web = {"candidates": [_candidate("c1", "Ada", "web", "")]}
    try:
        validate_research(web, pasted_leads="", search_enabled=True)
        raise AssertionError("expected a url failure")
    except GuardrailError as exc:
        assert "source_url" in str(exc)


def test_evaluator_rejects_invented_id_and_scores_missing_evidence_as_one():
    candidates = [_candidate("c1", "Ada")]
    try:
        validate_evaluations(
            {"evaluations": [{"candidate_id": "c2", "score": 3, "met_requirements": ["Python"], "missing_requirements": [], "evidence_note": "x"}]},
            candidates,
        )
        raise AssertionError("expected an invented id")
    except GuardrailError as exc:
        assert "not in the sourced list" in str(exc)
    rows = validate_evaluations(
        {"evaluations": [{"candidate_id": "c1", "score": 5, "met_requirements": [], "missing_requirements": [], "evidence_note": ""}]},
        candidates,
    )
    assert rows[0]["score"] == 1
    assert "evidence is missing" in rows[0]["evidence_note"].lower()


def test_ranking_orders_by_score_and_keeps_researcher_ties():
    candidates = [_candidate("c1", "Ada"), _candidate("c2", "Grace"), _candidate("c3", "Lin")]
    evaluations = [
        {"candidate_id": "c1", "score": 3, "met_requirements": ["Python"], "missing_requirements": ["Go"]},
        {"candidate_id": "c2", "score": 5, "met_requirements": ["Python"], "missing_requirements": []},
        {"candidate_id": "c3", "score": 3, "met_requirements": ["Python"], "missing_requirements": ["Go"]},
    ]
    ordered = canonical_order(candidates, evaluations)
    assert ordered == ["c2", "c1", "c3"]
    ranking = validate_recommendation(
        {"ordered_candidate_ids": ["c3", "c1"], "summary": "Grace is the strongest match.", "rows": []},
        candidates,
        evaluations,
    )
    assert ranking["ordered_candidate_ids"] == ["c2", "c1", "c3"]
    markdown = render_markdown("Ruby on Rails and React", ranking, "draft")
    assert "Contact decisions happen outside this product." in markdown
    assert "outreach" not in markdown.lower()
    assert "#### Sources" in markdown


def test_operator_supplied_candidates_must_appear_in_pasted_leads():
    pasted = "Ada Lovelace, ada@example.com, Rails engineer"
    accepted = validate_research(
        {"candidates": [{**_candidate("c1", "Ada Lovelace"), "email": "ada@example.com"}]},
        pasted_leads=pasted,
        search_enabled=False,
    )
    assert accepted[0]["name"] == "Ada Lovelace"
    assert accepted[0]["source_type"] == "operator-supplied"

    try:
        validate_research(
            {"candidates": [_candidate("c1", "Grace Hopper")]},
            pasted_leads=pasted,
            search_enabled=True,
        )
        raise AssertionError("expected a candidate missing from the pasted leads")
    except GuardrailError as exc:
        assert str(exc) == "Grace Hopper is not in the pasted leads."

    try:
        validate_research(
            {"candidates": [_candidate("c1", "Ada Lovelace")]},
            pasted_leads="   ",
            search_enabled=True,
        )
        raise AssertionError("expected rejection when no leads were pasted")
    except GuardrailError as exc:
        assert str(exc) == "Ada Lovelace is not in the pasted leads."

    try:
        validate_research(
            {
                "candidates": [
                    _candidate("c1", "Published Person", "web", "https://example.com/published"),
                    _candidate("c2", "Grace Hopper"),
                ]
            },
            pasted_leads="",
            search_enabled=True,
        )
        raise AssertionError("expected the operator-supplied candidate to be rejected")
    except GuardrailError as exc:
        assert str(exc) == "Grace Hopper is not in the pasted leads."


def test_recommendation_rejects_outreach_field_and_unknown_id():
    candidates = [_candidate("c1", "Ada")]
    evaluations = [{"candidate_id": "c1", "score": 4, "met_requirements": ["Python"], "missing_requirements": []}]
    try:
        validate_recommendation(
            {"ordered_candidate_ids": ["c1"], "summary": "A fit.", "outreach": "Hello"},
            candidates,
            evaluations,
        )
        raise AssertionError("expected outreach rejection")
    except GuardrailError as exc:
        assert "Outreach" in str(exc)
    try:
        validate_recommendation(
            {"ordered_candidate_ids": ["c9"], "summary": "A fit."},
            candidates,
            evaluations,
        )
        raise AssertionError("expected unknown id rejection")
    except GuardrailError as exc:
        assert "not in the sourced list" in str(exc)
