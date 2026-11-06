# Backend: Recruitment Assistant

## Actions

- `develop-be` — Python 3.13 backend, FastAPI process, file-backed runs, CrewAI 1.15.36.
- `define-agents` — Researcher, Evaluator, and Recommender in YAML, sequential, no delegation, no memory.
- `implement-endpoint` — Run, accept, discard, satisfaction, recommendation, health, and optional posting preview. There is no chat endpoint. The SAD specifies a form and a ranking, not a transcript.
- `document-backend` — This file.

`project-context/2.build/setup.md` is not in the repo. The SAD tells this persona to create the backend skeleton when `@project.mgr` is not assigned. That skeleton is `backend/`, `.env.example`, and the `backend/runs/` gitignore.

## Runtime

- AAMAD_TARGET_RUNTIME: crewai
- **CrewAI**: 1.15.36 (`crewai[tools]`). Requires Python `>=3.10,<3.14`. The machine default is Python 3.14.10, so the project venv is Python 3.13.18.
- **LLM**: `OPENAI_MODEL` from the environment, default `gpt-4o`. Temperature `0.2`. `max_tokens` `4096`.
- **Process**: `Process.sequential`. `memory=False`. `max_rpm=10`. `max_iter=12`. `max_retry_limit=2`. `guardrail_max_retries=2`.
- **Execution guard**: 900 seconds. CrewAI 1.15.36 has `max_execution_time` on `Agent`, not on `Crew`. Each agent starts with 900 seconds. After research, and again after evaluation, the remaining agents are reduced to the time left in that 900 seconds. Guardrails also reject a stage that has already passed the budget.
- **Function calling**: one `LLM` instance is assigned to every agent. `function_calling_llm` is deprecated in this CrewAI release and is not set. The mode is not switched during a run.
- **Tools**: `SerperDevTool` and `ScrapeWebsiteTool` bind only on the Researcher, and only when `SERPER_API_KEY` is non-empty. Evaluator and Recommender have no tools. `LinkedInTool` and `LI_AT` are not referenced.

## Files

| Path | Role |
| --- | --- |
| `backend/config/agents.yaml` | Researcher, Evaluator, Recommender role, goal, and backstory |
| `backend/config/tasks.yaml` | `research_candidates`, `evaluate_candidates`, `recommend_candidates` with context chaining |
| `backend/crew.py` | CrewAI crew, tool binding, kickoff, task callbacks |
| `backend/guardrails.py` | Deterministic checks and the markdown recommendation |
| `backend/app.py` | FastAPI routes |
| `backend/store.py` | `backend/runs/{run_id}/run.json` and `recommendation.md` |
| `backend/posting.py` | Optional F6 preview |
| `backend/trace.py` | Redacted prompt trace and task log |
| `backend/requirements.txt` | Direct pins |
| `backend/requirements.lock.txt` | Full environment pin (151 packages) |
| `backend/tests/` | Unit tests with a stubbed crew |

## Crew

Task order is fixed.

1. `research_candidates` has no context. It may return 1 to 10 candidates. Zero candidates is a failure. Pasted leads must show up as `operator-supplied`. An operator-supplied name must appear in the pasted text, and so must any email or phone on that row. An operator-supplied candidate is rejected when the paste is empty, including when search is on and other rows came from the web. Web rows require `source_url`. Search-off runs reject web rows.
2. `evaluate_candidates` receives the research task. Every sourced id is scored. An id that was not sourced fails the guardrail. Empty met and missing lists force score 1 and the note "The evidence is missing."
3. `recommend_candidates` receives both earlier tasks. Unknown ids and `outreach`, `email_draft`, or `inmail` fields fail the guardrail. The saved order is computed in code: score descending, ties keep Researcher order. The model writes the summary. The API renders `recommendation.md` from that JSON, including the line that contact decisions happen outside the product. The model cannot set `accepted`.

`Task.guardrail` returns `(False, message)` or `(True, normalized JSON)`. A failed guardrail retries up to `guardrail_max_retries`, then the run becomes `failed`. The failure is not filled with an invented candidate.

Callbacks write task-end events and move the run from `researching` to `evaluating` to `recommending` to `draft`. `source_elapsed_ms` is the wall time through the end of research.

If pasted leads are empty and `SERPER_API_KEY` is empty, kickoff does not call the model. The run fails at research with an explicit message.

Prompt traces go to `project-context/2.build/logs/prompt-{run_id}.json` before kickoff. Task events append to `trace.jsonl`. Both pass through redaction. Those log files are gitignored.

## API

Base URL `http://127.0.0.1:8000`. JSON only. No streaming. Errors:

```json
{"error": {"code": "validation_error", "message": "title is required.", "stage": null}}
```

| Method and path | Success | Failure |
| --- | --- | --- |
| `POST /api/runs` | `202` `{run_id, status: researching}` | `400` `validation_error`, `409` `run_in_progress` |
| `GET /api/runs/{run_id}` | `200` run document | `404` `run_not_found` |
| `POST /api/runs/{run_id}/accept` | `200` `accepted`, label, timestamp | `409` `invalid_state` unless status is `draft` |
| `POST /api/runs/{run_id}/discard` | `200` `discarded` | `409` unless `draft` |
| `POST /api/runs/{run_id}/satisfaction` | `200` score stored | `400` if score is not an integer 1–5; `409` until status is `draft`, `accepted`, or `discarded` |
| `GET /api/runs/{run_id}/recommendation` | `200` ranking and markdown when `accepted` | `404` otherwise |
| `POST /api/postings/preview` | `200` requisition fields, no run created | `400` if url and text are both set or both empty; `502` `posting_fetch_failed`. A URL body is streamed and reading stops once the next chunk would pass 1 MB |
| `GET /health` | `200` `{status: ok}` | Does not call the model |

`POST /api/runs` body:

```json
{
  "requisition": {
    "title": "",
    "description": "",
    "responsibilities": "",
    "requirements": "",
    "preferred_qualifications": "",
    "perks_and_benefits": ""
  },
  "pasted_leads": ""
}
```

Title and requirements are required. Requisition fields are capped at 20,000 characters. Pasted leads are capped at 50,000. A second start while a run is `researching`, `evaluating`, or `recommending` returns 409. Startup marks those leftover statuses `failed`, so a restarted process does not leave a run accepted.

The run document fields the frontend can poll are `status`, `requisition`, `pasted_leads`, `candidates`, `evaluations`, `ranking`, `recommendation_markdown`, `source_elapsed_ms`, `satisfaction`, `accepted_at`, `recruiter_label`, `discarded_at`, and `error`. Fields the crew has not produced are null.

Accept, discard, and satisfaction do not call the crew.

## How to run

From `recruitment-assistant`, with the Python 3.13 virtualenv:

```bash
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
.venv/bin/python -m pytest
```

That process serves the recruiter page at `/` and the hiring-manager page at `/hiring-manager`, plus the API. Create the venv again with Python 3.13 if needed, then install `backend/requirements.txt`. Do not bind `0.0.0.0`.

Fifteen tests passed on 2026-11-05. They cover F1 validation, the research and evaluation guardrails, operator-supplied names checked against the pasted leads, rank order, accept and discard, satisfaction, the single-run lock, recommendation visibility, posting-text preview, private URL rejection, the streamed 1 MB posting cap, stale-run recovery, secret redaction, and crew wiring. No test calls a model.

## Known gaps

- The optional CLI from the PRD is not in this slice. The pages are the required interface.
- This process serves the HTML pages at `/` and `/hiring-manager`. `@integration.eng` mounted them on this API. Opening the files from disk does not reach `/api`.
- A live model run was not executed. An unavailable model is handled as `failed` and is not marked `accepted`, but that path is not covered by a live call.
- Preferred-versus-required weighting is in the Evaluator prompt. The code does not parse which phrase is preferred. The PRD still has that as an open question.
- CrewAI checkpoint restore drops the method callbacks. This MVP does not resume a checkpointed crew.
- F6 URL preview checks the resolved address before the request, refuses redirects onto a blocked address, and ignores proxy environment variables. A DNS change between the check and the connection is still possible.

## Sources

- `project-context/1.define/prd.md`
- `project-context/1.define/sad.md`
- `.cursor/agents/backend-eng.md`
- `.cursor/rules/adapter-crewai.mdc`
- `.env.example`
- Installed package metadata for `crewai==1.15.36` (Python `<3.14,>=3.10`)
- No `setup.md`. No user stories.

## Assumptions

- `AAMAD_TARGET_RUNTIME` resolves to `crewai` from the PRD, the SAD, `.env.example`, and the operator request. `aamad.config.yml` is absent.
- `setup.md` is absent, so this epic created the backend skeleton.
- The SAD's file-per-run store is the MVP record. It is not a database. The persona line that forbids persistent storage is treated as "no database," and the SAD stays authoritative.
- Optional Serper search and the read-only posting preview are in the SAD API, so they are implemented. ATS writeback, messaging, and analytics are not.
- `OPENAI_MODEL` is the model name in `.env.example`. The code passes that value to CrewAI's `LLM`. It does not read `OPENAI_MODEL_NAME`.
- Temperature `0.2` and `max_tokens` `4096` are the Build controls the SAD left for this audit.
- Rank order and the markdown file are produced in Python from the guarded JSON so a model cannot attach outreach or mark a run accepted.
- Comment length 2,000 and recruiter-label length 200 are caps the SAD did not specify.
- `backend/runs/` is kept until the operator deletes it.

## Open Questions

- Carried from the PRD and SAD: time-to-source minute target, match-accuracy percentage, satisfaction average, whether a pasted-lead demo is enough, model spend cap, retention of run files, NYC or EU employment use, and whether a degree may outweigh skills.
- Is F6 URL fetch required for the first demo now that the endpoint exists? Pasted posting text and pasted requirements already run without it.
- Should `@security.eng` review this backend before Deliver? The example config asks for a security assessment. The PRD module map does not assign that persona.

## Audit

- **Timestamp**: 2026-11-05T21:13:00-08:00
- **Persona id**: `backend-eng`
- **Action**: `develop-be` review fixes
- AAMAD_TARGET_RUNTIME: crewai
- **LLM**: model from `OPENAI_MODEL`, default `gpt-4o`; temperature `0.2`; max_tokens `4096`
- **Crew controls**: sequential, memory false, max_iter 12, max_retry_limit 2, max_rpm 10, agent `max_execution_time` 900 seconds with a crew-level remaining-budget check
- **Model**: Grok 4.7, Cursor agent session. The application crew was not kicked off.
- **Inputs read**: `prd.md`, `sad.md`, `backend-eng.md`, `adapter-crewai.mdc`, `.env.example`. `setup.md` was missing.
- **Prompt Trace**: The operator asked for two review fixes before Step 3.5: reject operator-supplied candidates that are not in the pasted leads, including when no leads were pasted, and stop posting downloads while streaming once the size limit is exceeded. Regression tests were required, the backend tests were rerun, and this file was updated. System-prompt text is omitted.
- **Review fixes**: operator-supplied name, email, and phone are matched against the pasted leads; posting bodies are read with `iter_bytes` and the read stops before a chunk that would pass 1 MB is kept.
- **Tests**: `15 passed` via `.venv/bin/python -m pytest backend/tests`.
- **Output path**: `project-context/2.build/backend.md`
- **Handoff**: `@frontend.eng` can build the two pages against the API table. `@integration.eng` serves those pages from this process.

### 2026-11-05T21:54:10-08:00

- **Persona id**: `qa-eng`
- **Action**: correct the stale statement that this process does not serve the HTML pages
- AAMAD_TARGET_RUNTIME: crewai
- **What changed**: Known gaps and How to run now say this process serves `/` and `/hiring-manager`. The earlier audit remains the record of the backend session. No backend code was changed.
- **Prompt Trace**: Included in `project-context/2.build/qa.md`. System-prompt text is omitted.
