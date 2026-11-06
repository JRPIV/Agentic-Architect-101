"""Redact secret values before they reach logs or run files."""

from __future__ import annotations

import json
import os
import re
from typing import Any

_SECRET_NAME = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|COOKIE|CREDENTIAL)", re.I)
_SK_PATTERN = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{8,}")
_LI_AT = re.compile(r"(?i)li_at[=:\s]+[^\s,;]+")


def secret_values() -> list[str]:
    values: list[str] = []
    for name, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        if _SECRET_NAME.search(name):
            values.append(value)
    values.sort(key=len, reverse=True)
    return values


def redact_text(text: str) -> str:
    redacted = text
    for value in secret_values():
        redacted = redacted.replace(value, "[REDACTED]")
    redacted = _SK_PATTERN.sub("[REDACTED]", redacted)
    redacted = _BEARER.sub(r"\1[REDACTED]", redacted)
    redacted = _LI_AT.sub("li_at=[REDACTED]", redacted)
    return redacted


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {str(key): redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return redact_text(str(value))


def dumps(value: Any) -> str:
    return json.dumps(redact(value), ensure_ascii=False)
