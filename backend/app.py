"""FastAPI surface for one requisition at a time."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from backend.constants import (
    MAX_COMMENT_CHARS,
    MAX_LABEL_CHARS,
    MAX_PASTED_LEADS_CHARS,
    MAX_REQUISITION_CHARS,
)
from backend.posting import PostingError, preview_posting
from backend.runner import start
from backend.store import APIError, get_store

REQUISITION_FIELDS = (
    "title",
    "description",
    "responsibilities",
    "requirements",
    "preferred_qualifications",
    "perks_and_benefits",
)


class RequisitionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = ""
    description: str = ""
    responsibilities: str = ""
    requirements: str = ""
    preferred_qualifications: str = ""
    perks_and_benefits: str = ""


class CreateRunIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requisition: RequisitionIn
    pasted_leads: str = ""


class AcceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    recruiter_label: str


class SatisfactionIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    score: int
    comment: str = ""

    @field_validator("score")
    @classmethod
    def score_range(cls, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError("score must be an integer from 1 to 5")
        return value


class PreviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str | None = None
    text: str | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_store().fail_stale()
    yield


app = FastAPI(title="Recruitment Assistant", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/runs", status_code=202)
def create_run(body: CreateRunIn) -> JSONResponse:
    message = _validate_requisition(body.requisition) or _validate_length(
        "pasted_leads", body.pasted_leads, MAX_PASTED_LEADS_CHARS
    )
    if message:
        return _error("validation_error", message, 400, None)
    document = get_store().create(
        {field: getattr(body.requisition, field).strip() for field in REQUISITION_FIELDS},
        body.pasted_leads.strip(),
    )
    start(document["run_id"])
    return JSONResponse(
        status_code=202,
        content={"run_id": document["run_id"], "status": document["status"]},
    )


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> JSONResponse:
    document = get_store().read(run_id)
    return JSONResponse(content=document)


@app.post("/api/runs/{run_id}/accept")
def accept_run(run_id: str, body: AcceptIn) -> JSONResponse:
    label = body.recruiter_label.strip()
    if not label:
        return _error("validation_error", "recruiter_label is required.", 400, None)
    if len(label) > MAX_LABEL_CHARS:
        return _error("validation_error", "recruiter_label is too long.", 400, None)
    document = get_store().accept(run_id, label)
    return JSONResponse(content=document)


@app.post("/api/runs/{run_id}/discard")
def discard_run(run_id: str) -> JSONResponse:
    return JSONResponse(content=get_store().discard(run_id))


@app.post("/api/runs/{run_id}/satisfaction")
def save_satisfaction(run_id: str, body: SatisfactionIn) -> JSONResponse:
    comment = body.comment.strip()
    if len(comment) > MAX_COMMENT_CHARS:
        return _error("validation_error", "comment is too long.", 400, None)
    document = get_store().save_satisfaction(run_id, body.score, comment)
    return JSONResponse(content=document)


@app.get("/api/runs/{run_id}/recommendation")
def get_recommendation(run_id: str) -> JSONResponse:
    document = get_store().read(run_id)
    if document["status"] != "accepted":
        return _error("invalid_state", "The recommendation is not accepted.", 404, None)
    return JSONResponse(
        content={
            "run_id": document["run_id"],
            "ranking": document["ranking"],
            "markdown": document["recommendation_markdown"],
        }
    )


@app.post("/api/postings/preview")
def preview(body: PreviewIn) -> JSONResponse:
    has_url = bool(body.url and body.url.strip())
    has_text = bool(body.text and body.text.strip())
    if has_url == has_text:
        return _error("validation_error", "Provide a posting url or pasted posting text, not both.", 400, None)
    try:
        requisition = preview_posting(url=body.url, text=body.text)
    except PostingError as exc:
        return _error("posting_fetch_failed", exc.message, 502, None)
    return JSONResponse(content={"requisition": requisition})


@app.exception_handler(APIError)
def handle_api_error(_request: Any, exc: APIError) -> JSONResponse:
    return _error(exc.code, exc.message, exc.status_code, exc.stage)


@app.exception_handler(RequestValidationError)
def handle_request_validation(_request: Any, exc: RequestValidationError) -> JSONResponse:
    return _validation_response(exc)


@app.exception_handler(ValidationError)
def handle_validation_error(_request: Any, exc: ValidationError) -> JSONResponse:
    return _validation_response(exc)


def _validate_requisition(requisition: RequisitionIn) -> str | None:
    for field in ("title", "requirements"):
        if not getattr(requisition, field).strip():
            return f"{field} is required."
    for field in REQUISITION_FIELDS:
        message = _validate_length(field, getattr(requisition, field), MAX_REQUISITION_CHARS)
        if message:
            return message
    return None


def _validate_length(field: str, value: str, limit: int) -> str | None:
    if len(value) > limit:
        return f"{field} exceeds {limit} characters."
    return None


def _validation_response(exc: ValidationError | RequestValidationError) -> JSONResponse:
    field = _field_name(exc)
    if field == "score":
        message = "score must be an integer from 1 to 5."
    elif field == "recruiter_label":
        message = "recruiter_label is required."
    elif field:
        message = f"{field} is invalid."
    else:
        message = "Request body is invalid."
    return _error("validation_error", message, 400, None)


def _field_name(exc: ValidationError | RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return ""
    location = errors[0].get("loc") or ()
    parts = [str(part) for part in location if part not in {"body"}]
    return parts[-1] if parts else ""


def _error(code: str, message: str, status_code: int, stage: str | None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "stage": stage}},
    )
