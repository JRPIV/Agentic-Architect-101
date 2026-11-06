"""File-backed run records. One JSON document and one markdown file per run."""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.constants import ACTIVE_STATUSES, DRAFT_STATUSES
from backend.guardrails import replace_status_line


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int, stage: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.stage = stage


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._lock = threading.Lock()

    def fail_stale(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self._lock:
            for path in self.root.glob("*/run.json"):
                document = json.loads(path.read_text(encoding="utf-8"))
                if document.get("status") in ACTIVE_STATUSES:
                    self._fail_unlocked(
                        document,
                        "The process restarted before this run finished.",
                        document.get("status"),
                    )

    def create(self, requisition: dict[str, str], pasted_leads: str) -> dict[str, Any]:
        self.root.mkdir(parents=True, exist_ok=True)
        with self._lock:
            for path in self.root.glob("*/run.json"):
                document = json.loads(path.read_text(encoding="utf-8"))
                if document.get("status") in ACTIVE_STATUSES:
                    raise APIError(
                        "run_in_progress",
                        "A run is already in progress.",
                        409,
                        None,
                    )
            run_id = str(uuid.uuid4())
            document = {
                "run_id": run_id,
                "status": "researching",
                "requisition": requisition,
                "pasted_leads": pasted_leads,
                "candidates": None,
                "evaluations": None,
                "ranking": None,
                "recommendation_markdown": None,
                "source_elapsed_ms": None,
                "satisfaction": None,
                "accepted_at": None,
                "recruiter_label": None,
                "discarded_at": None,
                "error": None,
                "created_at": _now(),
                "updated_at": _now(),
            }
            self._write_unlocked(document)
            return document

    def read(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            return self._read_required(run_id)

    def update(self, run_id: str, **fields: Any) -> dict[str, Any]:
        with self._lock:
            document = self._read_required(run_id)
            document.update(fields)
            document["updated_at"] = _now()
            self._write_unlocked(document)
            return document

    def fail(self, run_id: str, stage: str, message: str) -> dict[str, Any] | None:
        with self._lock:
            path = self._run_path(run_id)
            if not path.exists():
                return None
            document = json.loads(path.read_text(encoding="utf-8"))
            if document.get("status") not in ACTIVE_STATUSES:
                return document
            self._fail_unlocked(document, message, stage)
            return document

    def accept(self, run_id: str, recruiter_label: str) -> dict[str, Any]:
        with self._lock:
            document = self._read_required(run_id)
            if document["status"] != "draft":
                raise APIError(
                    "invalid_state",
                    "Only a draft recommendation can be accepted.",
                    409,
                    _stage(document),
                )
            document["status"] = "accepted"
            document["accepted_at"] = _now()
            document["recruiter_label"] = recruiter_label
            document["updated_at"] = document["accepted_at"]
            self._rewrite_markdown(document)
            self._write_unlocked(document)
            return document

    def discard(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            document = self._read_required(run_id)
            if document["status"] != "draft":
                raise APIError(
                    "invalid_state",
                    "Only a draft recommendation can be discarded.",
                    409,
                    _stage(document),
                )
            document["status"] = "discarded"
            document["discarded_at"] = _now()
            document["updated_at"] = document["discarded_at"]
            self._rewrite_markdown(document)
            self._write_unlocked(document)
            return document

    def save_satisfaction(self, run_id: str, score: int, comment: str) -> dict[str, Any]:
        with self._lock:
            document = self._read_required(run_id)
            if document["status"] not in DRAFT_STATUSES:
                raise APIError(
                    "invalid_state",
                    "A satisfaction score can be saved after a draft exists.",
                    409,
                    _stage(document),
                )
            document["satisfaction"] = {"score": score, "comment": comment, "recorded_at": _now()}
            document["updated_at"] = document["satisfaction"]["recorded_at"]
            self._write_unlocked(document)
            return document

    def _fail_unlocked(self, document: dict[str, Any], message: str, stage: str | None) -> None:
        public_stage = stage if stage in {"research", "evaluation", "recommendation"} else _stage(document)
        document["status"] = "failed"
        document["error"] = {"code": "crew_failed", "message": message, "stage": public_stage}
        document["updated_at"] = _now()
        self._write_unlocked(document)

    def _rewrite_markdown(self, document: dict[str, Any]) -> None:
        markdown = document.get("recommendation_markdown")
        if isinstance(markdown, str):
            document["recommendation_markdown"] = replace_status_line(markdown, document["status"])

    def _read_required(self, run_id: str) -> dict[str, Any]:
        path = self._run_path(run_id)
        if not path.exists():
            raise APIError("run_not_found", "Run not found.", 404, None)
        return json.loads(path.read_text(encoding="utf-8"))

    def _run_path(self, run_id: str) -> Path:
        try:
            normalized = str(uuid.UUID(run_id))
        except ValueError as exc:
            raise APIError("run_not_found", "Run not found.", 404, None) from exc
        return self.root / normalized / "run.json"

    def _write_unlocked(self, document: dict[str, Any]) -> None:
        directory = self.root / document["run_id"]
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "run.json"
        temporary = directory / "run.json.tmp"
        temporary.write_text(json.dumps(document, indent=2), encoding="utf-8")
        os.replace(temporary, target)
        markdown = document.get("recommendation_markdown")
        if isinstance(markdown, str):
            markdown_path = directory / "recommendation.md"
            markdown_temporary = directory / "recommendation.md.tmp"
            markdown_temporary.write_text(markdown, encoding="utf-8")
            os.replace(markdown_temporary, markdown_path)


_store: RunStore | None = None


def get_store() -> RunStore:
    global _store
    if _store is None:
        configured = os.environ.get("BACKEND_RUNS_DIR")
        root = Path(configured) if configured else project_root() / "backend" / "runs"
        _store = RunStore(root)
    return _store


def reset_store() -> None:
    global _store
    _store = None


def _stage(document: dict[str, Any]) -> str | None:
    status = document.get("status")
    if status in {"researching", "failed"} and not document.get("candidates"):
        return "research"
    if status == "evaluating":
        return "evaluation"
    if status == "recommending":
        return "recommendation"
    error = document.get("error") or {}
    return error.get("stage")
