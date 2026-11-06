"""JSON contracts and deterministic checks for crew task output."""

from __future__ import annotations

import json
import re
from typing import Any

from backend.constants import MAX_CANDIDATES

OUTREACH_KEYS = ("outreach", "email_draft", "inmail")
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class GuardrailError(ValueError):
    """A task output failed a deterministic check."""


def parse_payload(result: Any) -> Any:
    if hasattr(result, "pydantic") and result.pydantic is not None:
        model = result.pydantic
        if hasattr(model, "model_dump"):
            return model.model_dump()
    raw = result.raw if hasattr(result, "raw") else result
    if isinstance(raw, (dict, list)):
        return raw
    text = _FENCE.sub("", str(raw).strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GuardrailError("Task output is not JSON.") from exc


def _reject_outreach(payload: Any) -> None:
    if isinstance(payload, dict):
        for key in payload:
            if str(key).lower() in OUTREACH_KEYS:
                raise GuardrailError(f"Outreach field '{key}' is not allowed.")
        for value in payload.values():
            _reject_outreach(value)
    elif isinstance(payload, list):
        for item in payload:
            _reject_outreach(item)


def validate_research(
    result: Any,
    *,
    pasted_leads: str,
    search_enabled: bool,
) -> list[dict[str, Any]]:
    payload = parse_payload(result)
    _reject_outreach(payload)
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(candidates, list):
        raise GuardrailError("Research output needs a candidates list.")
    has_leads = bool(pasted_leads.strip())
    if not candidates:
        if not has_leads:
            raise GuardrailError(
                "No pasted leads and no sourced candidates. The Researcher does not invent people."
            )
        raise GuardrailError("Pasted leads were provided, but the candidate list is empty.")
    if len(candidates) > MAX_CANDIDATES:
        raise GuardrailError(f"Candidate list has {len(candidates)} people. The maximum is {MAX_CANDIDATES}.")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    operator_supplied = 0
    for index, item in enumerate(candidates, start=1):
        if not isinstance(item, dict):
            raise GuardrailError("Each candidate must be an object.")
        name = str(item.get("name") or "").strip()
        summary = str(item.get("summary") or "").strip()
        source_type = str(item.get("source_type") or "").strip()
        source_url = str(item.get("source_url") or "").strip()
        if not name or not summary:
            raise GuardrailError("Each candidate needs a name and a summary from the source text.")
        if source_type not in {"operator-supplied", "web"}:
            raise GuardrailError("source_type must be operator-supplied or web.")
        if source_type == "web" and not source_url.startswith("http"):
            raise GuardrailError(f"{name} is a web lead and needs a source_url.")
        if source_type == "operator-supplied":
            source_url = ""
            operator_supplied += 1
            _require_in_pasted_leads(name, pasted_leads, f"{name} is not in the pasted leads.")
            email = _optional_text(item.get("email"))
            phone = _optional_text(item.get("phone"))
            if email:
                _require_in_pasted_leads(email, pasted_leads, f"{name} email is not in the pasted leads.")
            if phone:
                _require_in_pasted_leads(phone, pasted_leads, f"{name} phone is not in the pasted leads.")
        else:
            email = _optional_text(item.get("email"))
            phone = _optional_text(item.get("phone"))
        candidate_id = str(item.get("id") or f"c{index}").strip() or f"c{index}"
        if candidate_id in seen:
            raise GuardrailError(f"Duplicate candidate id {candidate_id}.")
        seen.add(candidate_id)
        normalized.append(
            {
                "id": candidate_id,
                "name": name,
                "summary": summary,
                "source_type": source_type,
                "source_url": source_url,
                "email": email,
                "phone": phone,
            }
        )
    if has_leads and operator_supplied == 0:
        raise GuardrailError("Pasted leads must appear as operator-supplied candidates.")
    if not search_enabled and any(item["source_type"] == "web" for item in normalized):
        raise GuardrailError("Search is off, so web candidates are not allowed.")
    return normalized


def validate_evaluations(result: Any, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload = parse_payload(result)
    _reject_outreach(payload)
    rows = payload.get("evaluations") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise GuardrailError("Evaluation output needs an evaluations list.")
    allowed = [item["id"] for item in candidates]
    allowed_set = set(allowed)
    by_id: dict[str, dict[str, Any]] = {}
    for item in rows:
        if not isinstance(item, dict):
            raise GuardrailError("Each evaluation must be an object.")
        candidate_id = str(item.get("candidate_id") or "").strip()
        if candidate_id not in allowed_set:
            raise GuardrailError(f"Evaluation id {candidate_id or '(blank)'} is not in the sourced list.")
        if candidate_id in by_id:
            raise GuardrailError(f"Duplicate evaluation for {candidate_id}.")
        score = item.get("score")
        met = item.get("met_requirements")
        missing = item.get("missing_requirements")
        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
            raise GuardrailError(f"{candidate_id} needs an integer score from 1 to 5.")
        if not isinstance(met, list) or not isinstance(missing, list):
            raise GuardrailError(f"{candidate_id} needs met_requirements and missing_requirements lists.")
        note = str(item.get("evidence_note") or "").strip()
        met_text = [_phrase(value) for value in met if _phrase(value)]
        missing_text = [_phrase(value) for value in missing if _phrase(value)]
        if not met_text and not missing_text:
            score = 1
            if "evidence is missing" not in note.lower():
                note = "The evidence is missing."
        by_id[candidate_id] = {
            "candidate_id": candidate_id,
            "score": score,
            "met_requirements": met_text,
            "missing_requirements": missing_text,
            "evidence_note": note,
        }
    missing_ids = [candidate_id for candidate_id in allowed if candidate_id not in by_id]
    if missing_ids:
        raise GuardrailError("Evaluations are missing sourced ids: " + ", ".join(missing_ids))
    return [by_id[candidate_id] for candidate_id in allowed]


def canonical_order(candidates: list[dict[str, Any]], evaluations: list[dict[str, Any]]) -> list[str]:
    position = {item["id"]: index for index, item in enumerate(candidates)}
    scores = {item["candidate_id"]: int(item["score"]) for item in evaluations}
    return sorted(position, key=lambda candidate_id: (-scores[candidate_id], position[candidate_id]))


def validate_recommendation(
    result: Any,
    candidates: list[dict[str, Any]],
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = parse_payload(result)
    _reject_outreach(payload)
    if not isinstance(payload, dict):
        raise GuardrailError("Recommendation output must be a JSON object.")
    summary = str(payload.get("summary") or "").strip()
    if not summary:
        raise GuardrailError("Recommendation needs a summary.")
    ordered = canonical_order(candidates, evaluations)
    by_candidate = {item["id"]: item for item in candidates}
    by_eval = {item["candidate_id"]: item for item in evaluations}
    model_ids = payload.get("ordered_candidate_ids")
    if isinstance(model_ids, list):
        for candidate_id in model_ids:
            if str(candidate_id) not in by_candidate:
                raise GuardrailError(f"Ranking id {candidate_id} is not in the sourced list.")
    rows = []
    for candidate_id in ordered:
        candidate = by_candidate[candidate_id]
        evaluation = by_eval[candidate_id]
        rows.append(
            {
                "candidate_id": candidate_id,
                "name": candidate["name"],
                "source_type": candidate["source_type"],
                "source_url": candidate["source_url"],
                "score": evaluation["score"],
                "met_requirements": evaluation["met_requirements"],
                "missing_requirements": evaluation["missing_requirements"],
            }
        )
    return {"ordered_candidate_ids": ordered, "summary": summary, "rows": rows}


def render_markdown(title: str, ranking: dict[str, Any], status: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"Status: {status}",
        "",
        "This ranking supports the recruiter and the hiring manager. Contact decisions happen outside this product.",
        "",
        "## Summary",
        "",
        ranking["summary"],
        "",
    ]
    for index, row in enumerate(ranking["rows"], start=1):
        source = row["source_type"]
        if row["source_url"]:
            source = f"{source} {row['source_url']}"
        met = ", ".join(row["met_requirements"]) or "None recorded"
        missing = ", ".join(row["missing_requirements"]) or "None recorded"
        lines.extend(
            [
                f"### {index}. {row['name']}",
                "",
                "#### Sources",
                "",
                source,
                "",
                "#### Scores",
                "",
                str(row["score"]),
                "",
                "#### Gaps",
                "",
                f"Met requirements: {met}",
                "",
                f"Missing requirements: {missing}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def replace_status_line(markdown: str, status: str) -> str:
    return re.sub(r"^Status: .+$", f"Status: {status}", markdown, count=1, flags=re.M)


def _require_in_pasted_leads(value: str, pasted_leads: str, message: str) -> None:
    if not _appears_in_source(pasted_leads, value):
        raise GuardrailError(message)


def _appears_in_source(source: str, value: str) -> bool:
    folded_source = " ".join(source.casefold().split())
    folded_value = " ".join(value.casefold().split())
    if not folded_value:
        return False
    return re.search(rf"(?<!\w){re.escape(folded_value)}(?!\w)", folded_source) is not None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _phrase(value: Any) -> str:
    return str(value).strip()
