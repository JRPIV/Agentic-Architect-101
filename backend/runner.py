"""Start one crew run in the background. Tests can replace the executor."""

from __future__ import annotations

import threading
from collections.abc import Callable

from backend.redact import redact_text
from backend.store import get_store
from backend.trace import write_event

Executor = Callable[[str], None]


def default_execute(run_id: str) -> None:
    from backend.crew import kickoff_run

    kickoff_run(run_id)


_executor: Executor = default_execute


def set_executor(executor: Executor) -> None:
    global _executor
    _executor = executor


def reset_executor() -> None:
    global _executor
    _executor = default_execute


def start(run_id: str) -> None:
    thread = threading.Thread(target=_safe, args=(run_id,), name=f"run-{run_id}", daemon=True)
    thread.start()


def _safe(run_id: str) -> None:
    try:
        _executor(run_id)
    except Exception as exc:
        get_store().fail(run_id, "research", redact_text(f"{exc.__class__.__name__}: {exc}"))
        write_event({"run_id": run_id, "event": "task_failed", "error_class": exc.__class__.__name__})
