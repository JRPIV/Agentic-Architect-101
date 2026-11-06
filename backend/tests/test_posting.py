"""Posting download stops at the size limit instead of buffering the whole body."""

import httpx

from backend.constants import POSTING_MAX_BYTES
from backend.posting import PostingError, fetch_posting


class _CountingStream(httpx.SyncByteStream):
    def __init__(self, pieces: list[bytes], counter: dict[str, int]) -> None:
        self._pieces = pieces
        self._counter = counter

    def __iter__(self):
        for piece in self._pieces:
            self._counter["count"] += 1
            yield piece

    def close(self) -> None:
        return None


def _client_with(handler, monkeypatch):
    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("backend.posting.httpx.Client", factory)
    monkeypatch.setattr("backend.posting._assert_public_https", lambda _url: None)


def test_fetch_stops_when_stream_exceeds_size_limit(monkeypatch):
    counter = {"count": 0}
    chunk = b"x" * (POSTING_MAX_BYTES // 2 + 1)
    pieces = [chunk for _ in range(6)]

    def handler(_request):
        return httpx.Response(
            200,
            headers={"content-type": "text/plain"},
            stream=_CountingStream(pieces, counter),
        )

    _client_with(handler, monkeypatch)
    try:
        fetch_posting("https://jobs.example/posting")
        raise AssertionError("expected the size limit to stop the download")
    except PostingError as exc:
        assert "1 MB" in str(exc)
    assert counter["count"] < len(pieces)


def test_fetch_reads_a_stream_that_fits(monkeypatch):
    counter = {"count": 0}
    pieces = [b"Staff Engineer\n", b"Requirements\n", b"Python\n"]

    def handler(_request):
        return httpx.Response(
            200,
            headers={"content-type": "text/plain"},
            stream=_CountingStream(pieces, counter),
        )

    _client_with(handler, monkeypatch)
    text, _title = fetch_posting("https://jobs.example/posting")
    assert text == "Staff Engineer\nRequirements\nPython\n"
    assert counter["count"] == len(pieces)
