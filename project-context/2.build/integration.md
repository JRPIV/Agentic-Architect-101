# Integration: Recruitment Assistant

## Actions

| Action | Result |
| --- | --- |
| `integrate-api` | FastAPI serves the existing pages and static files on the same origin as the API |
| `verify-messageflow` | Browser round-trip: posting preview, then a run that fails at research without calling the model. Hiring-manager page reads that run |
| `log-integration` | This file |

## Decisions

The integration persona file says to connect a Next.js chat UI to a chat endpoint. The PRD, SAD AD-2, and SAD AD-3 override that. The MVP is two desktop pages, a form, and a ranking. Kickoff is non-streaming. The page polls. There is no chat transcript and no chat route.

`frontend/js/api.js` already calls the Section 4 paths with `fetch` against the page origin. This epic did not change that client. Serving the files from the API process is the wire: the browser and the API share `http://127.0.0.1:8000`, so no CORS layer and no second port were added.

No inbox, pipeline, analytics, messaging, or ATS route was added. No new third-party client was added. F6 pasted-text preview was already on the API and is what the recruiter page calls. F6 URL fetch was not exercised in the browser.

`setup.md` is absent. `aamad.config.yml` is absent.

## What the process serves

| Path | File |
| --- | --- |
| `/` | `frontend/index.html` |
| `/hiring-manager` | `frontend/hiring-manager.html` |
| `/css/app.css` | `frontend/css/app.css` |
| `/js/api.js` | `frontend/js/api.js` |
| `/js/render.js` | `frontend/js/render.js` |
| `/js/recruiter.js` | `frontend/js/recruiter.js` |
| `/js/hiring-manager.js` | `frontend/js/hiring-manager.js` |

Page routes return the HTML files. CSS and JS are mounted only under `/css` and `/js`. Those mounts do not cover `/api` or `/health`.

## Runtime contract

- **AAMAD_TARGET_RUNTIME**: `crewai`. Unset in this agent shell. Resolved from the SAD, the PRD, and the adapter registry default.
- **Streaming**: none. `POST /api/runs` returns `202` with `{run_id, status: researching}` as soon as the run file exists. The recruiter page and the hiring-manager page poll `GET /api/runs/{run_id}` every 2 seconds while status is `researching`, `evaluating`, or `recommending`.
- **Create body**: `requisition` (title, description, responsibilities, requirements, preferred_qualifications, perks_and_benefits) and `pasted_leads`. Title and requirements are required.
- **Accept body**: `{recruiter_label}`. Discard is a POST with no body. Satisfaction is `{score, comment}` with `score` an integer 1–5.
- **Preview body**: `{url}` or `{text}`, not both. The response is `{requisition}` and does not create a run.
- **Recommendation**: `GET /api/runs/{run_id}/recommendation` returns ranking and markdown only when status is `accepted`. Otherwise `404`.
- **Error envelope**:

```json
{"error": {"code": "validation_error", "message": "title is required.", "stage": null}}
```

`code` is one of `validation_error`, `run_in_progress`, `run_not_found`, `invalid_state`, `crew_failed`, `posting_fetch_failed`. `stage` is `research`, `evaluation`, `recommendation`, or null. The client reads `error.message` and `error.stage`.

The checked client paths are only `POST /api/runs`, `GET /api/runs/{run_id}`, `POST /api/runs/{run_id}/accept`, `POST /api/runs/{run_id}/discard`, `POST /api/runs/{run_id}/satisfaction`, `GET /api/runs/{run_id}/recommendation`, and `POST /api/postings/preview`.

## How to run

From `recruitment-assistant`, with the Python 3.13 virtualenv:

```bash
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/hiring-manager`. Do not bind `0.0.0.0`. Opening the HTML files from disk does not reach `/api`.

A run with empty pasted leads does not call the model when `SERPER_API_KEY` is empty. It fails at research with "No pasted leads and search is off. The Researcher does not invent people."

## Verification

`16 passed` via `.venv/bin/python -m pytest backend/tests`. The new check is `test_pages_share_the_api_origin`: both pages return HTML, the script and stylesheet load, preview does not create a run, a stubbed run reaches `failed` at research, and the recommendation stays `404`.

Browser check against `http://127.0.0.1:8000`, with `SERPER_API_KEY` empty in that process:

- `/` returned the recruiter page. Run, Accept, Discard, and Save score started disabled. `/css/app.css`, `/js/api.js`, `/js/render.js`, and `/js/recruiter.js` loaded from the same origin.
- Pasted posting text for a Staff Engineer role called `POST /api/postings/preview` (`200`). Title became "Staff Engineer", requirements became "Python and FastAPI", and responsibilities were filled. Status stayed "no run yet." The page said the crew had not started.
- Run called `POST /api/runs` (`202`) and then `GET /api/runs/{run_id}`. The page showed "Status: failed. Stage: research. No pasted leads and search is off. The Researcher does not invent people." The run id was `cbfa82af-20b5-478a-8813-3fe0629da6bd`, kept in `?run_id=`. Accept, Discard, and Save score stayed disabled. No candidate was rendered.
- `/hiring-manager?run_id=` for that id loaded `hiring-manager.js` and called `GET /api/runs/{run_id}`. It showed the same failure and stage. The ranking container was empty. The page has no Accept control. `GET /api/runs/{run_id}/recommendation` returned `404` `invalid_state`.
- No `prompt-{run_id}.json` was written. The early research return did not call the model.

## Known gaps

- A live model run was not executed. Accept, discard, and satisfaction were not clicked in the browser. Those transitions are covered by the stubbed API test, which drives the same routes the pages call. A draft with a real crew still needs pasted leads or `SERPER_API_KEY`, plus a model credential.
- `frontend.md` and `backend.md` still say this process does not serve the pages. This file is the record that it does.
- The hiring-manager page still uses the full run document to tell draft, discarded, and failed apart. No status-only route was added.
- The optional CLI is not served.
- F6 URL preview was not clicked. Existing API tests reject a private posting URL and a non-public example URL. Pasted posting text is the demo path.
- The persona's chat and streaming assumptions do not apply. CrewAI kickoff stays one non-streaming call per run.

## Sources

- `project-context/1.define/prd.md` (F1–F6, UX, out of scope, Module 06 map)
- `project-context/1.define/sad.md` (AD-2, AD-3, Sections 3, 4, and 6)
- `project-context/2.build/backend.md`
- `project-context/2.build/frontend.md`
- `.cursor/agents/integration-eng.md`
- `.cursor/rules/adapter-crewai.mdc`
- `.cursor/rules/adapter-registry.mdc`
- No `setup.md`. No `aamad.config.yml`. No user stories.

## Assumptions

- `AAMAD_TARGET_RUNTIME` was unset in this agent shell. It resolves to `crewai`.
- The operator asked for this as Step 5 and pointed at the integration persona. This artifact is that persona's output. QA is still the next epic.
- Same-origin static files are the integration. The existing `fetch` client did not need a rewrite.
- An empty-lead failure is a valid basic round-trip for the demo. It proves the page, the create call, the poll, and the hiring-manager read without spending a model call.
- Poll interval stays 2 seconds, as the frontend already implemented. The SAD requires polling and does not name an interval.
- `frontend.md` and `backend.md` were left in place. Their "pages are not served" lines are stale after this epic.

## Open Questions

- Carried from the PRD and SAD: time-to-source minute target, match-accuracy percentage, satisfaction average, retention, NYC or EU employment use, and whether a degree may outweigh skills.
- Should a later epic add a status-only response so the hiring-manager page can distinguish draft, discarded, and failed without receiving the draft ranking?
- Is a pasted-lead demo enough for the first live crew run, or is Serper required?
- Is the 2-second poll interval acceptable for a run that may last up to the 15-minute guard?

## Audit

- **Timestamp**: 2026-11-05T21:38:24-08:00
- **Persona id**: `integration-eng`
- **Action**: `integrate-api`, `verify-messageflow`, `log-integration`
- **AAMAD_TARGET_RUNTIME**: `crewai`
- **Runtime warning**: `AAMAD_TARGET_RUNTIME` was unset in this agent shell and `aamad.config.yml` was not present. Resolved to `crewai` from the SAD, the PRD, and `.cursor/rules/adapter-registry.mdc`.
- **Streaming**: non-streaming JSON. The UI polls. No token stream was added.
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed and were not set. The application crew was not kicked off. The checked run returned before `kickoff`.
- **Inputs read**: `prd.md`, `sad.md`, `backend.md`, `frontend.md`, `integration-eng.md`, `backend/app.py`, `frontend/js/api.js`, and the page scripts those files name. `setup.md` was missing.
- **Tool use**: edits to `backend/app.py` and `backend/tests/test_api.py`. Pytest. A local uvicorn process on `127.0.0.1:8000` for the browser check, then stopped. No secret values were written.
- **Tests**: `16 passed` via `.venv/bin/python -m pytest backend/tests`.
- **Prompt Trace**: The operator asked to complete Step 5, review the PRD, SAD, backend.md, and frontend.md, serve the existing frontend from FastAPI at `/` and `/hiring-manager`, wire the existing API calls, verify a basic round-trip, keep the scope minimal, and document results and gaps in this file. System-prompt text is omitted.
- **Output path**: `project-context/2.build/integration.md`
- **Handoff**: `@qa.eng` can run the process with the command above. The pages and the API are the same origin. A live draft still needs pasted leads or search, and a model credential.
