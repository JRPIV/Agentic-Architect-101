"""Prompt trace, task lifecycle logs, and process logs.

Request and crew lines keep metadata. Secret values and candidate text stay out.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from backend.redact import dumps
from backend.store import project_root

_EVENT_FIELDS = (
    "event",
    "run_id",
    "task",
    "stage",
    "error_class",
    "source_elapsed_ms",
    "search_enabled",
)
_configured = False


def log_dir() -> Path:
    configured = os.environ.get("BACKEND_LOG_DIR")
    path = Path(configured) if configured else project_root() / "project-context" / "2.build" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


class _AppFileHandler(logging.Handler):
    """Append to the current log directory. Tests change that directory per case."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            with (log_dir() / "app.log").open("a", encoding="utf-8") as handle:
                handle.write(self.format(record) + "\n")
        except Exception:
            self.handleError(record)


def get_logger() -> logging.Logger:
    global _configured
    logger = logging.getLogger("recruitment")
    if _configured:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    file_handler = _AppFileHandler()
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    _configured = True
    return logger


def write_event(event: dict) -> None:
    line = dumps(event)
    with (log_dir() / "trace.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    safe = json.loads(line)
    parts: list[str] = []
    for key in _EVENT_FIELDS:
        if key not in safe:
            continue
        parts.append(f"{key}={safe[key]}")
    tools = safe.get("tools")
    if isinstance(tools, list):
        parts.append("tools=" + ",".join(str(name) for name in tools))
    level = logging.ERROR if safe.get("event") == "task_failed" else logging.INFO
    get_logger().log(level, "crew %s", " ".join(parts))


def write_prompt_trace(run_id: str, payload: dict) -> None:
    (log_dir() / f"prompt-{run_id}.json").write_text(dumps(payload) + "\n", encoding="utf-8")
