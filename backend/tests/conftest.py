import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKEND_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("BACKEND_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    from backend.runner import reset_executor
    from backend.store import reset_store

    reset_store()
    reset_executor()
    from backend.app import app

    with TestClient(app) as test_client:
        yield test_client
    reset_executor()
    reset_store()
