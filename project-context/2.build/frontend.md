# Frontend: Recruitment Assistant

## Actions

| Action | Result |
| --- | --- |
| `develop-fe` | Recruiter page, hiring-manager page, and a same-origin `fetch` client for the Section 4 API |
| `style-ui` | One desktop stylesheet. No Tailwind and no component library, per SAD AD-2 |
| `add-placeholders` | Not done. SAD Interface Requirements says future-work placeholders are not screens |
| `document-frontend` | This file |

## Decisions

The frontend persona file says to build a Next.js chat UI and to leave the API client to integration. SAD AD-2 and the PRD User Experience section override that. The MVP is two desktop pages and a ranking view, not a chat transcript. SAD Section 3 also assigns the API client to this epic. This epic does not import CrewAI, read `.env`, or mount the files on FastAPI. Integration later serves these files from that same API process.

The optional CLI is out of this slice. SAD Assumptions say the two pages satisfy the PRD.

`setup.md` is absent. `aamad.config.yml` is absent. The SAD remains the UI contract.

## Pages

| File | Route integration should serve | Audience |
| --- | --- | --- |
| `frontend/index.html` | `/` | Recruiter |
| `frontend/hiring-manager.html` | `/hiring-manager` | Hiring manager |
| `frontend/css/app.css` | `/css/app.css` | Both |
| `frontend/js/api.js` | `/js/api.js` | Both |
| `frontend/js/render.js` | `/js/render.js` | Both |
| `frontend/js/recruiter.js` | `/js/recruiter.js` | Recruiter |
| `frontend/js/hiring-manager.js` | `/js/hiring-manager.js` | Hiring manager |

Script and stylesheet URLs are root-absolute so they still resolve when `/hiring-manager` has no trailing slash.

### Recruiter page

- Requirement fields: title, description, responsibilities, requirements, preferred qualifications, perks and benefits. Title and requirements are required. Run stays disabled until both have text, and an API validation error is shown with the field name.
- Optional pasted leads.
- Optional posting URL or pasted posting text. Fill fields calls `POST /api/postings/preview` with one of those values. It does not create a run. A failed preview leaves the form editable.
- Run calls `POST /api/runs`, then polls `GET /api/runs/{run_id}` every 2 seconds while status is `researching`, `evaluating`, or `recommending`.
- Status text names the stage (`research`, `evaluation`, `recommendation`) or the terminal status. Failures include the stage and the API message. Color is not the only signal.
- Source time shows `source_elapsed_ms` once the API records it.
- Sourced candidates show name, `source_type`, and an http(s) source URL when one exists.
- Evaluations show score, met requirements, missing requirements, and the evidence note.
- The ranking table keeps API row order. The page states that the ranking supports the recruiter and the hiring manager and that contact decisions happen outside the product. There is no outreach or send control.
- Accept sends `recruiter_label` and is available only for `draft`. Discard asks for a second click, then sends an empty `POST`. Both stay disabled outside `draft`.
- Satisfaction is a 1–5 choice plus an optional comment. Save is enabled only for `draft`, `accepted`, or `discarded`.
- The run id is kept in `?run_id=` so a refresh resumes the same run. A link points at `/hiring-manager?run_id=`.

### Hiring-manager page

- Opens one `run_id` from the query string. It does not list runs.
- No Run, Accept, or Discard controls.
- `draft`: says the run is not accepted yet and does not render the ranking.
- `accepted`: renders the ranking from `GET /api/runs/{run_id}/recommendation`.
- `discarded`: says the run is not a recommendation and does not render it.
- `failed`: shows the stage and the message.
- Polls only while the run is `researching`, `evaluating`, or `recommending`. Check again reloads a selected run.

## Client

`frontend/js/api.js` calls these paths and no others:

- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `POST /api/runs/{run_id}/accept`
- `POST /api/runs/{run_id}/discard`
- `POST /api/runs/{run_id}/satisfaction`
- `GET /api/runs/{run_id}/recommendation`
- `POST /api/postings/preview`

Requests use the page origin. There is no streaming client. SAD AD-3 is the reason: kickoff is non-streaming, and the page polls. The 15-minute crew guard is an API limit; the page keeps polling until the status leaves the active set or the run is missing.

Rendered candidate and ranking text is assigned with `textContent`. A source URL becomes a link only when its protocol is `http` or `https`.

## Traceability

| PRD | UI |
| --- | --- |
| F1 Submit job requirements | Recruiter form, disabled Run until title and requirements exist, API field error |
| F2 Candidate search | Sourced list, source label, source URL, source time |
| F3 Automated evaluation | Evaluation list with score, met, and missing requirements |
| F4 Ranked recommendations | Draft ranking, Accept, Discard, hiring-manager page for accepted only |
| F5 Recruiter satisfaction | 1–5 score after a draft exists |
| F6 Job posting intake | Preview fills the same fields and does not start the crew |
| Out of scope: ATS, messaging, analytics | No inbox, pipeline, analytics, or send control |

## How to view

The API process serves these files. From `recruitment-assistant`:

```bash
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/hiring-manager`. Opening the HTML files from disk does not reach `/api`.

## Verification

Checked in a browser against the running API, with search forced off for that process so an empty-lead run could not call the model:

- Run stays disabled until title and requirements are present. Accept, Discard, and Save score start disabled.
- Pasted posting text fills title, requirements, and responsibilities and leaves status at "no run yet."
- A posting URL and pasted text together are rejected on the page and do not start the crew.
- A run with requirements and no pasted leads ends as `failed`, stage `research`, with the API reason. Accept and Save score stay disabled.
- A draft shows source time, the operator-supplied candidate, the evaluation, and the ranked row. Saving 4 stores "Saved satisfaction score: 4 of 5."
- Before accept, the hiring-manager page says the run is not accepted yet and does not show the candidate.
- Accept with a recruiter label sets `accepted` and disables Accept and Discard. The hiring-manager page then shows the ranked row, source, score, met requirements, and missing requirements.
- Discard keeps the draft readable on the recruiter page. The hiring-manager page says it is not a recommendation and does not show the candidate.

## Known gaps

- FastAPI serves the pages. That wiring is recorded in `integration.md`.
- The optional CLI is not in this slice.
- The hiring-manager page reads `GET /api/runs/{run_id}` so it can tell draft, discarded, and failed apart. That response includes draft fields. The page does not render them unless `GET /api/runs/{run_id}/recommendation` returns 200.
- There is no frontend test file. The browser pass above is the check for this slice.

## Sources

- `project-context/1.define/prd.md` (F1–F6, UX, out of scope)
- `project-context/1.define/sad.md` (AD-2, AD-3, Section 3, Section 4)
- `.cursor/agents/frontend-eng.md`
- `project-context/2.build/backend.md` (run document fields and the API table the handoff names for this page)
- No `setup.md`. No `aamad.config.yml`. No user stories.

## Assumptions

- `AAMAD_TARGET_RUNTIME` was not set in this agent shell. It resolves to `crewai` from the SAD, the PRD, and the adapter registry default.
- `setup.md` was not created because `@project.mgr` is not in the PRD module map. The backend skeleton already exists.
- SAD scope wins over the persona file's Next.js chat default and over its ban on an API client. The persona ban on mounting or starting the backend still holds.
- Poll interval is 2 seconds. The SAD requires polling and does not name an interval.
- A second click before Discard is an inline confirmation, not a new feature and not a modal.
- `?run_id=` on the recruiter page is a refresh handle. It is not a run index.
- F6 pasted text uses `POST /api/postings/preview`, which the backend already implements and which does not create a run.
- Comment and recruiter-label length limits follow the backend caps of 2,000 and 200. Requisition fields use the SAD cap of 20,000, and pasted leads use 50,000.

## Open Questions

- Carried from the PRD and SAD: time-to-source minute target, match-accuracy percentage, satisfaction average, retention, NYC or EU employment use, and whether a degree may outweigh skills.
- Should integration add a status-only response so the hiring-manager page can distinguish draft, discarded, and failed without receiving the draft ranking?
- Is the 2-second poll interval acceptable for a run that may last up to the 15-minute guard?

## Audit

- **Timestamp**: 2026-11-05T21:35:00-08:00
- **Persona id**: `frontend-eng`
- **Action**: `develop-fe`, `style-ui`, `document-frontend`
- AAMAD_TARGET_RUNTIME: crewai
- **Runtime warning**: `AAMAD_TARGET_RUNTIME` was unset in this agent shell and `aamad.config.yml` was not present. Resolved to `crewai` from the SAD, the PRD, and `.cursor/rules/adapter-registry.mdc`.
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed and were not set. No application crew was kicked off.
- **Inputs read**: `project-context/1.define/prd.md`, `project-context/1.define/sad.md`, `.cursor/agents/frontend-eng.md`. `setup.md` was missing. The backend API table in `project-context/2.build/backend.md` was read so the client matches the run document the backend handoff names.
- **Tool use**: file writes for `frontend/` and this artifact. A local preview process served the static files and forwarded `/api` to the existing FastAPI process for the browser check. Shell was used for that check. At the time of this frontend session the pages were not mounted on FastAPI. Integration later mounted them. No secret values were written.
- **Prompt Trace**: The operator asked for the frontend persona to review the PRD and SAD, implement the MVP web interface, and document decisions in `project-context/2.build/frontend.md` using `develop-fe`. System-prompt text is omitted.
- **Output path**: `project-context/2.build/frontend.md`
- **Handoff**: `@integration.eng` can serve `frontend/` from the API process at `/` and `/hiring-manager`. Do not add inbox, pipeline, or analytics routes.

### 2026-11-05T21:54:10-08:00

- **Persona id**: `qa-eng`
- **Action**: correct the stale statements that the pages are not served
- AAMAD_TARGET_RUNTIME: crewai
- **What changed**: How to view, Known gaps, and the decisions paragraph now say the API process serves the pages. The frontend session's audit stays the record of that session. No frontend code was changed.
- **Prompt Trace**: Included in `project-context/2.build/qa.md`. System-prompt text is omitted.
