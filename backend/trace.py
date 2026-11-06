"""Prompt trace and task lifecycle logs. Secret values are removed first."""

from __future__ import annotations

import os
from pathlib import Path

from backend.redact import dumps
from backend.store import project_root


def log_dir() -> Path:
    configured = os.environ.get("BACKEND_LOG_DIR")
    path = Path(configured) if configured else project_root() / "project-context" / "2.build" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_event(event: dict) -> None:
    with (log_dir() / "trace.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(dumps(event) + "\n")


def write_prompt_trace(run_id: str, payload: dict) -> None:
    (log_dir() / f"prompt-{run_id}.json").write_text(dumps(payload) + "\n", encoding="utf-8")
