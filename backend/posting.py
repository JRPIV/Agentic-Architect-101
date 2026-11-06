"""Read-only job-posting preview. This does not create a run."""

from __future__ import annotations

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from backend.constants import (
    MAX_REQUISITION_CHARS,
    POSTING_MAX_BYTES,
    POSTING_MAX_REDIRECTS,
    POSTING_TIMEOUT_SECONDS,
)

_SECTION_NAMES = {
    "description": "description",
    "about the role": "description",
    "responsibilities": "responsibilities",
    "responsibility": "responsibilities",
    "what you'll do": "responsibilities",
    "requirements": "requirements",
    "required qualifications": "requirements",
    "qualifications": "requirements",
    "preferred qualifications": "preferred_qualifications",
    "preferred": "preferred_qualifications",
    "nice to have": "preferred_qualifications",
    "perks and benefits": "perks_and_benefits",
    "perks": "perks_and_benefits",
    "benefits": "perks_and_benefits",
}


class PostingError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._in_title:
            self.title_parts.append(data)
        self.parts.append(data)


def preview_posting(*, url: str | None, text: str | None) -> dict[str, str]:
    has_url = bool(url and url.strip())
    has_text = bool(text and text.strip())
    if has_url == has_text:
        raise PostingError("Provide a posting url or pasted posting text, not both.")
    if has_text:
        return parse_posting(text or "")
    body, title = fetch_posting(url or "")
    return parse_posting(body, title_hint=title)


def parse_posting(text: str, title_hint: str = "") -> dict[str, str]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    title = title_hint.strip()
    sections: dict[str, list[str]] = {
        "description": [],
        "responsibilities": [],
        "requirements": [],
        "preferred_qualifications": [],
        "perks_and_benefits": [],
    }
    current = "description"
    saw_heading = False
    for line in lines:
        if not line:
            continue
        key = _SECTION_NAMES.get(line.lower().rstrip(":"))
        if key:
            current = key
            saw_heading = True
            continue
        if not title and not saw_heading:
            title = line
            continue
        sections[current].append(line)
    if not title:
        title = title_hint.strip()
    return {
        "title": _clip(title),
        "description": _clip("\n".join(sections["description"])),
        "responsibilities": _clip("\n".join(sections["responsibilities"])),
        "requirements": _clip("\n".join(sections["requirements"])),
        "preferred_qualifications": _clip("\n".join(sections["preferred_qualifications"])),
        "perks_and_benefits": _clip("\n".join(sections["perks_and_benefits"])),
    }


def fetch_posting(url: str) -> tuple[str, str]:
    current = url.strip()
    visited = 0
    while True:
        _assert_public_https(current)
        try:
            with httpx.Client(timeout=POSTING_TIMEOUT_SECONDS, follow_redirects=False, trust_env=False) as client:
                with client.stream("GET", current) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        visited += 1
                        if visited > POSTING_MAX_REDIRECTS:
                            raise PostingError("The posting URL redirected too many times.")
                        location = response.headers.get("location")
                        if not location:
                            raise PostingError("The posting URL redirected without a location.")
                        current = urljoin(current, location)
                        continue
                    if response.status_code >= 400:
                        raise PostingError(f"The posting URL returned HTTP {response.status_code}.")
                    content_type = response.headers.get("content-type", "")
                    body = _read_capped(response.iter_bytes())
                    encoding = response.encoding
        except PostingError:
            raise
        except httpx.HTTPError as exc:
            raise PostingError("The posting URL could not be read.") from exc
        text = body.decode(encoding or "utf-8", errors="replace")
        if "html" in content_type or "<html" in text[:500].lower():
            return _html_to_text(text)
        return text, ""


def _read_capped(chunks) -> bytes:
    """Stop reading as soon as the next chunk would pass the size limit."""
    received = bytearray()
    for chunk in chunks:
        if not chunk:
            continue
        if len(received) + len(chunk) > POSTING_MAX_BYTES:
            raise PostingError("The posting page is larger than 1 MB.")
        received.extend(chunk)
    return bytes(received)


def _html_to_text(html: str) -> tuple[str, str]:
    parser = _TextExtractor()
    parser.feed(html)
    title = " ".join(part.strip() for part in parser.title_parts if part.strip())
    body = "\n".join(part.strip() for part in "".join(parser.parts).splitlines())
    return body, title


def _assert_public_https(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise PostingError("Only https posting URLs are allowed.")
    if parsed.username or parsed.password:
        raise PostingError("Posting URLs cannot include credentials.")
    host = parsed.hostname
    if not host:
        raise PostingError("The posting URL needs a host.")
    if host.lower() == "localhost":
        raise PostingError("The posting URL points at a blocked address.")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    addresses: list[ipaddress.IPv4Address | ipaddress.IPv6Address]
    if literal is not None:
        addresses = [literal]
    else:
        try:
            infos = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise PostingError("The posting host could not be resolved.") from exc
        addresses = [ipaddress.ip_address(info[4][0]) for info in infos]
    if not addresses or any(_blocked(address) for address in addresses):
        raise PostingError("The posting URL points at a blocked address.")


def _blocked(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def _clip(value: str) -> str:
    return value[:MAX_REQUISITION_CHARS]
