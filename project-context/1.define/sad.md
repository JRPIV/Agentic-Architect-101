# System Architecture Document: Recruitment Assistant

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md`  
**MRD**: `project-context/1.define/mrd.md`  
**User Stories**: None. `project-context/1.define/user-stories/` is absent.  
**MVP Scope**: One requisition, three sequential agents, recruiter form, hiring-manager read view, file-backed run record. Optional job-posting URL preview is specified and may be deferred inside Module 06 (PRD Open Questions).  
**Selected Runtime**: `crewai`

This SAD is the blueprint for Module 06. It does not authorize application code by itself. Review it before `@backend.eng`, `@frontend.eng`, or `@integration.eng` implement.

## 1. MVP Architecture Philosophy & Principles

### Stakeholders and Concerns

| Stakeholder | Concern | Where this SAD answers it |
| --- | --- | --- |
| Recruiter | A shortlist for one role, with sources and reasons, without sending messages | Crew tasks, `POST /api/runs`, recruiter page |
| Hiring manager | Ranked recommendations only after the recruiter accepts | `GET /api/runs/{run_id}/recommendation`, hiring-manager page |
| Module 06 builders | A small crew, a stable JSON contract, and a single process | Sections 2–4 and 6 |
| QA | Tests for F1–F5, the three PRD metrics, and the out-of-scope boundaries | Section 9 |
| Operator | Secrets stay out of git and logs; rankings of people are drafts until accepted | Section 8 |

### MVP Design Principles

- Deliver the recruiter’s first reviewable shortlist before any extra product surface.
- Three agents, sequential CrewAI, no delegation, no memory. That is the smallest orchestration that still keeps search, evaluation, and ranking inspectable (PRD Application Crew Definition).
- Observable by default: task start and stop, tool names, Researcher elapsed time, and errors, with secrets redacted (PRD Infrastructure Specifications).
- Deploy scaffolding (lint, test, build, health check, runbook) belongs to Module 07. This SAD defines the shape. It does not start a deploy.

### Core vs Future Features

**MVP (P0, PRD F1–F5)**

- Submit one requisition and optional pasted leads.
- Researcher sources at most 10 candidates.
- Evaluator scores only those candidates.
- Recommender writes a ranked draft.
- Recruiter accepts or discards. Hiring manager reads accepted rankings only.
- Recruiter stores a 1–5 satisfaction score on the run.
- Record Researcher elapsed time.

**Optional inside the mini-project (PRD F6)**

- Read-only preview of a job-posting URL or pasted posting text into the same requisition fields. Pasted text needs no new service. URL fetch is a separate call that must not start the crew.

**Future / excluded**

- Full ATS integration, candidate communication, advanced analytics (PRD Out of Scope).
- LinkedIn session cookies, Selenium login, crew `train`, SSO, multi-tenant hosting, bias-audit program, commercial launch.
- Chat transcript as the primary UI. The PRD specifies a form and a ranking view.
- A database, more than one active crew run, and horizontal scaling.

### Technical Architecture Decisions

| ID | Decision | Rationale |
| --- | --- | --- |
| AD-1 | Python 3 backend, one process, FastAPI for HTTP | CrewAI’s adapter is Python. FastAPI gives request validation and `GET /health` without a second service. |
| AD-2 | Two desktop pages, no chat UI, no required component library | PRD User Experience: a recruiter form and a hiring-manager view. The template’s chat default does not apply. |
| AD-3 | Non-streaming kickoff; the page polls run status | A crew run is a multi-minute job (15-minute guard). Polling matches “one run at a time” and the stage status line. |
| AD-4 | CrewAI sequential YAML crew; accept/discard is API state, not `human_input` | PRD: a failed model call must not mark the report accepted. The crew stops at `draft`. |
| AD-5 | One JSON file plus one markdown file per run; no database | PRD: files are enough for the recommendation and the satisfaction score. |
| AD-6 | Search and page-reader tools bind only when `SERPER_API_KEY` is set, and only on the Researcher | PRD least privilege. Evaluator and Recommender have no tools. |
| AD-7 | Bind the HTTP server to localhost for the mini-project | PRD has no login. A local bind is the control that matches “whoever can start the process.” |

## 2. Multi-Agent System Specification

### Agent Architecture Requirements

Three agents. `allow_delegation=false`. `memory=false`. `max_iter <= 12`. `max_retry_limit >= 2`. Process: `sequential`. No manager agent and no hierarchical process.

| Agent | Role | Goal | Tools | Collaborates by |
| --- | --- | --- | --- | --- |
| `researcher` | Candidate Researcher | Source candidates for the submitted job requirements | `SerperDevTool` and `ScrapeWebsiteTool` only when `SERPER_API_KEY` is set. Never `LinkedInTool`. Never `LI_AT`. | Writes the candidate list the Evaluator must use |
| `evaluator` | Candidate Evaluator | Score each sourced candidate against the job criteria | None | Reads Researcher output only. Adds no people |
| `recommender` | Candidate Recommender | Rank those evaluations for the recruiter and the hiring manager | None | Reads Researcher and Evaluator outputs. Does not draft outreach |

Backstories and the 1–5 score rule, including “preferred qualifications cannot outweigh missing required skills,” stay as written in the PRD. The crew does not send email, InMail, or calendar invites.

### Task / Turn Orchestration

Configuration files, per the CrewAI adapter:

- `backend/config/agents.yaml`
- `backend/config/tasks.yaml`
- `backend/crew.py`

| Task id | Agent | Context | Expected output |
| --- | --- | --- | --- |
| `research_candidates` | `researcher` | none | JSON candidate list, max 10, plus the stage elapsed time recorded by the API around the task |
| `evaluate_candidates` | `evaluator` | `research_candidates` | JSON evaluations for the same ids only |
| `recommend_candidates` | `recommender` | `research_candidates`, `evaluate_candidates` | JSON ranking and a markdown recommendation with no code fence and no outreach section |

Execution flow:

1. API validates F1 fields and creates a run in `researching`.
2. `research_candidates` runs. If search is off and pasted leads are empty, the task fails and the run becomes `failed`. The crew does not invent people.
3. On success, status becomes `evaluating`, then `recommend_candidates` runs after evaluation (`recommending`).
4. API checks the guardrails below. On pass, status becomes `draft`. On fail, status becomes `failed` with the stage name.
5. Recruiter accept or discard updates status. The crew does not run again for that decision.
6. A new submission creates a new `run_id`. It does not flip an older run to `accepted`.

**Researcher JSON (machine contract)**

Each candidate:

- `id` (stable within the run)
- `name`
- `summary` (profile text actually read or pasted)
- `source_type`: `operator-supplied` or `web`
- `source_url`: required when `source_type` is `web`; empty when operator-supplied
- `email` and `phone`: included only when present in pasted text or on the cited page

List length is 1 to 10 when the stage succeeds. Zero results with no pasted leads is a failure, not an empty success.

**Evaluator JSON**

For every Researcher `id`, and no others:

- `candidate_id`
- `score` integer 1–5
- `met_requirements` (list of requirement phrases from the requisition)
- `missing_requirements` (list)
- `evidence_note`

No usable evidence forces `score` 1 and an `evidence_note` that says the evidence is missing.

**Recommender JSON**

- `ordered_candidate_ids` (score descending; ties keep Researcher list order)
- `summary` (short text for the hiring manager)
- Each row repeats `source_type`, `source_url`, `score`, `met_requirements`, `missing_requirements`

The markdown body is derived from that JSON. It has headings for the requisition title, sources, scores, and gaps. It has no outreach heading and no send control. The API sets `status`. The model output must not set `accepted`.

**Guardrails**

- Researcher: reject unknown people with no source, reject lists longer than 10, reject web rows without `source_url`.
- Evaluator: reject any `candidate_id` absent from the Researcher list, reject missing scores or missing met/missing lists.
- Recommender: reject ids that fail the same subset check, reject outreach language fields if the model adds them (`outreach`, `email_draft`, `inmail`).
- Adapter: `Task.guardrail` (or equivalent post-check in `crew.py` if the installed CrewAI build has no guardrail hook) halts the run on failure. Do not fill a failed stage with an unsourced candidate.

**Errors, retries, cancellation**

- Tool failures retry up to `max_retry_limit` (at least 2), then fail the task with tool name and error class.
- Crew `max_execution_time` is 900 seconds (PRD 15-minute engineering guard, not the time-to-source target).
- `max_iter` 12 on each agent.
- `max_rpm` 10 at crew level until a spend cap is chosen (Assumption).
- One active run. A second start returns HTTP 409. There is no cancel API in the MVP. Stopping the process stops the run. The on-disk status stays `failed` if the process dies mid-run and restarts (the file is not left `accepted`).
- Kickoff is one requisition. Do not use `kickoff_for_each`.

**Runtime-conditional configuration (crewai)**

- Crew composition: `researcher`, `evaluator`, `recommender` only.
- Process: `Process.sequential`.
- YAML under `backend/config/`.
- Context chaining as in the task table.
- `memory=False`. Do not set `CREWAI_STORAGE_DIR`.
- Function-calling mode, if used, stays fixed for the run and is recorded in the Build audit.
- Prompt Trace for each kickoff is written under `project-context/2.build/logs` with secrets redacted, not committed as source.

Claude Agent SDK and Cursor SDK subsections do not apply. `AAMAD_TARGET_RUNTIME` resolves to `crewai`.

## 3. Frontend Architecture Specification

### Technology Stack

- Pages: static HTML, CSS, and a small `fetch` client.
- No mandatory UI library and no chat framework.
- Type safety: the JSON contract in Section 4 is the type boundary. A TypeScript app is not required for the MVP.
- State: the run document from `GET /api/runs/{run_id}` is the only client state that matters. Poll while status is `researching`, `evaluating`, or `recommending`.

This stack is an SAD default. The PRD does not name a frontend framework.

### Application Structure

| Route | Audience | Behavior |
| --- | --- | --- |
| `/` | Recruiter | F1 fields, optional pasted leads, optional posting URL, Run, stage status, elapsed source time, sourced list, evaluations, draft ranking, Accept, Discard, satisfaction score |
| `/hiring-manager?run_id=` | Hiring manager | Accepted ranking only. No Run, Accept, or Discard |

The frontend epic builds these pages and a client module that calls the paths in Section 4. It does not import CrewAI or read `.env`. The integration epic serves the pages from the same process as the API and checks the wiring.

Desktop layout only. Status text names the stage (`research`, `evaluation`, `recommendation`) and does not rely on color alone. Failures show the stage and a plain-language reason.

### Interface Requirements

- Missing title or requirements: the Run control stays disabled or the API error is shown with the field name. The crew does not start.
- In-progress: stage name and, once research finishes, the recorded elapsed time.
- `draft`: full recruiter detail. Hiring-manager route shows that the run is not accepted yet.
- `accepted`: both pages can show the ranking. Hiring manager sees scores, sources, met requirements, and missing requirements.
- `discarded`: recruiter can still read the draft. Hiring manager does not see it as a recommendation.
- `failed`: message and stage. Status is not `accepted`.
- Satisfaction: 1–5 plus optional comment, enabled once a draft exists (`draft`, `accepted`, or `discarded`).
- Future Work placeholders are not screens. Do not add inbox, pipeline, or analytics nav items.

A CLI that prints the same recommendation is allowed by the PRD. It is optional and reads the same run file. The pages remain required.

## 4. Backend Architecture Specification

### API Architecture

Base path `/api`. JSON in and out. No token streaming. Errors:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Requirements are required.",
    "stage": null
  }
}
```

`code` is one of `validation_error`, `run_in_progress`, `run_not_found`, `invalid_state`, `crew_failed`, `posting_fetch_failed`. `stage` is `research`, `evaluation`, `recommendation`, or null.

| Method and path | PRD | Request | Response |
| --- | --- | --- | --- |
| `POST /api/runs` | F1, F2 start | `requisition` (title, description, responsibilities, requirements, preferred_qualifications, perks_and_benefits), optional `pasted_leads` | `202` `{ "run_id", "status": "researching" }` or `400` / `409` |
| `GET /api/runs/{run_id}` | F2–F5 | none | Run document: requisition, candidates, evaluations, ranking, `status`, `source_elapsed_ms`, `satisfaction`, `error` |
| `POST /api/runs/{run_id}/accept` | F4 | `{ "recruiter_label": string }` | `200` status `accepted` with timestamp. `409` unless current status is `draft`. Label required |
| `POST /api/runs/{run_id}/discard` | F4 | empty body | `200` status `discarded`. `409` unless `draft` |
| `POST /api/runs/{run_id}/satisfaction` | F5 | `{ "score": 1-5, "comment": "" }` | `200` stored score. `409` until a draft has existed |
| `GET /api/runs/{run_id}/recommendation` | F4 hiring manager | none | Ranking JSON and markdown only when `accepted`. Otherwise `404` |
| `POST /api/postings/preview` | F6 optional | `{ "url": "https://..." }` or `{ "text": "..." }` | Requisition field object. Does not create a run. `502` `posting_fetch_failed` on URL failure |
| `GET /health` | Module 07 | none | `{ "status": "ok" }` |

Validation: title and requirements are non-empty strings. Score is an integer 1–5. `pasted_leads` is plain text, capped at 50_000 characters. Requisition fields capped at 20_000 characters each. No rate limit beyond the single-run lock. A second `POST /api/runs` while a run is `researching`, `evaluating`, or `recommending` returns `409` `run_in_progress`.

The run document is the response schema both frontend and backend share. Fields the crew has not produced yet are null.

### Data Architecture

No database. Each run is a directory `backend/runs/{run_id}/`:

- `run.json` — the API document
- `recommendation.md` — markdown after a successful recommend task, including drafts

`run_id` is a UUID. `backend/runs/` is gitignored. Retention is “until the operator deletes the directory” until the PRD retention question is answered.

Accept writes `accepted_at` and `recruiter_label` into `run.json`. Discard writes `discarded_at`. Satisfaction writes `score` and `comment`. These writes are the only status transitions after `draft`, and they do not call the crew.

### Runtime Integration Layer

- `POST /api/runs` persists the requisition, then starts the crew in the same process (background task). The HTTP call returns `202` as soon as the run file exists.
- `crew.py` loads YAML, binds tools from the environment, calls `kickoff` once with `job_requirements` text and `pasted_leads`.
- The API updates `status` at each task boundary so the poll reflects research, evaluation, or recommendation.
- `source_elapsed_ms` is the wall time around `research_candidates` only.
- Prompt Trace and task lifecycle logs go to `project-context/2.build/logs`. The run file stores task outputs, not raw secrets.
- If the model endpoint is unavailable, the run ends `failed` and stays unaccepted.

### Authentication & Secrets

No login and no session cookie for users. Protection for the mini-project is localhost binding plus filesystem permissions on `backend/runs/`.

`.env.example` names only:

| Name | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Yes for the example model path | Model provider credential. The upstream example uses GPT-4o. Build may change the provider and must then record the real variable name in `setup.md`. |
| `OPENAI_MODEL_NAME` | No | Model id. Build records the resolved value in its audit. |
| `SERPER_API_KEY` | No | Enables Researcher search and page reader. Absent means pasted leads only. |

`LI_AT` is not a variable. Do not add it.

## 5. DevOps & Deployment Architecture

### CI/CD

Module 07 adds a pipeline that runs lint, unit test, and build for the Python backend and the static frontend. The pipeline does not deploy on push. The PRD does not authorize a live deploy.

### Hosting

Smallest target: one local process.

- Listen on `127.0.0.1:8000`.
- Serve the API and the two pages.
- `GET /health` returns `200` when the process is up. It does not call the model.

A single container is allowed in Module 07 if it runs that same process. Multi-region, autoscaling, and IaC are Future Work.

### Observability

Baseline: structured logs for task start, task end, tool name, retries, `source_elapsed_ms`, and error class. No APM. Logs and Prompt Trace redact environment values and cookie-like strings.

## 6. Data Flow & Integration Architecture

```text
Recruiter page
    |  POST /api/runs
    v
FastAPI  --writes run.json (researching)-->  backend/runs/{id}/
    |
    v
CrewAI sequential
    research_candidates  --optional Serper + scrape-->  public web
    evaluate_candidates  --no tools-->
    recommend_candidates --no tools-->
    |
    v
run.json status=draft, recommendation.md
    |
    +--> Recruiter polls GET /api/runs/{id}
    +--> POST accept | discard | satisfaction
    |
    v
Hiring manager GET /api/runs/{id}/recommendation
    only if status=accepted
```

External calls in the MVP:

- Model provider (required to complete a real run).
- Serper search and page fetch (only when `SERPER_API_KEY` is set).
- Optional F6: one HTTP GET of a posting URL, then map text into requisition fields. No write to that site.

Pasted leads and pasted posting text stay inside the process. They are not an integration.

Errors surface as the error envelope and as `run.status=failed` with `stage` and `message`. The page shows that text. Guardrail failures use `crew_failed`.

## 7. Performance & Scalability Specifications

- Concurrency: one crew run per process.
- Time to source: measured as `source_elapsed_ms`. No pass/fail minute target (PRD Open Questions).
- Engineering stop: 900 seconds for the whole crew. Hitting it fails the run with the active stage name.
- Token control: `max_iter` 12, `max_rpm` 10, and the output caps in Section 4. Build logs token usage per QA run when the provider reports it. No dollar cap exists yet.
- Scaling path: deferred. A queue and more workers wait until the PRD allows more than one run.

## 8. Security & Compliance Architecture

MVP controls:

- **Identity.** No accounts. The process binds to localhost so it is not a public screening service. Do not bind `0.0.0.0` in the mini-project.
- **Secrets.** Provider and search keys come from the environment. They are absent from source, `run.json`, markdown, Prompt Trace, and logs.
- **Least-privilege tools.** Only the Researcher can call the network, and only through the two optional tools. Evaluator and Recommender cannot browse.
- **No LinkedIn session.** The example `LinkedInTool` and `LI_AT` are not dependencies. QA looks for those names.
- **No outbound candidate contact.** No SMTP, email API, or messaging client is in the dependency set. Recommendation JSON rejects outreach fields.
- **Human gate.** `accepted` is written only by `POST /api/runs/{id}/accept` from `draft`, with a recruiter label and a timestamp. Crew output cannot set it.
- **Ranking label.** Markdown states that the list supports the recruiter and the hiring manager and that contact decisions happen outside the product (PRD Security).
- **Input validation.** Required fields, length caps, score range, and status checks on accept, discard, and satisfaction.
- **SSRF, if F6 URL preview is built.** Allow `https` only, block private, loopback, and link-local addresses, set a short timeout, and cap the response body (1 MB). A failed fetch leaves the form editable and does not start a run.
- **PII.** `run.json` may contain names and profile URLs. The directory is local and gitignored. Retention is an open question, not a silent policy of “keep forever” beyond this MVP default.
- **Supply chain.** Pin backend dependencies in the Build lockfile. Do not add the example’s Selenium LinkedIn client.

Compliance that stays out of this mini-project, and must stay visible:

- NYC Local Law 144 (bias audit and candidate notice) if a score substantially assists screening of NYC candidates.
- EU AI Act high-risk employment classification for job matching and ranking, as described in the MRD, if the ranking is used that way.
- This SAD is not a legal opinion. Using `accepted` rankings as an automated employment decision is outside the mini-project’s compliance design. The product behavior required here is a labeled draft plus an explicit accept action on localhost.

`@security.eng` is in the AAMAD epic index and is not in the PRD Module 06 map. Section 9 still recommends that assessment before Module 07 because the files hold personal data and a ranking.

## 9. Testing & Quality Assurance Specifications

Unit tests (no live model):

- F1 validation rejects a missing title or requirements and names the field.
- Researcher guardrail rejects an empty list when no leads were pasted, a list over 10, a web candidate without a URL, and an id the Evaluator invents.
- Score 1 when evidence is missing.
- Ranking order is score descending, with ties in Researcher order.
- Accept from `draft` stores label and time. Accept from `failed` or `researching` returns `invalid_state`. Discard does not set `accepted`.
- Satisfaction rejects scores outside 1–5 and rejects a run that never reached `draft`.
- Recommendation GET returns 404 until `accepted`.
- A second run start while one is active returns 409.
- Log fixtures contain no `OPENAI_API_KEY` or `SERPER_API_KEY` values.

Integration and smoke:

- One scripted requisition (the example Ruby on Rails and React role, pasted leads, no search key) walks F1–F5 with a stubbed crew and shows `source_elapsed_ms`.
- With search enabled, every `web` candidate in an accepted run has `source_url`.
- QA counts messages sent by the product as zero and confirms there is no analytics view beyond the single ranking.
- Map at least one test to each P0 acceptance criterion in the PRD.

Runtime checks: task ids, YAML tool names resolve before kickoff, and a down model ends `failed` rather than `accepted`.

Security assessment before Deliver is recommended even though the PRD leaves `@security.eng` as an open assignment.

## 10. MVP Launch & Feedback Strategy

There is no commercial launch and no beta program (PRD Section 9). A pilot is one recruiter running one requisition locally and showing an accepted ranking to one hiring manager.

Success for that pilot is the three PRD metrics:

- Time to source is visible on the run.
- Every ranked candidate is in the sourced list and has met and missing requirements.
- A 1–5 satisfaction score is stored.

After the first local run, fix guardrail failures and empty-search behavior before any optional F6 URL fetch or Module 07 hosting work.

## Implementation Guidance for AI Development Agents

1. `@project.mgr` is not assigned by the PRD. If that persona is added, `setup.md` creates `backend/`, `frontend/`, `.env.example`, and the runs gitignore from this SAD. Until then, `@backend.eng` creates that skeleton as part of the crew epic.
2. `@frontend.eng` builds the two pages and the API client against Section 4. No CrewAI import.
3. `@backend.eng` adds the YAML crew, guardrails, run files, and FastAPI routes.
4. `@integration.eng` serves the pages from the API process and, if F6 is in the build, the posting preview.
5. `@qa.eng` validates Section 9 and writes `project-context/2.build/qa.md`.
6. `@devops.eng` in Module 07 packages CI, the localhost (or single-container) run, and the runbook. No live deploy without a new operator decision.

## Architecture Validation Checklist

- [x] PRD F1–F5 mapped to pages, routes, crew tasks, and tests
- [x] F6 preview specified as optional and unable to start the crew or write back to a posting system
- [x] Agents are Researcher, Evaluator, and Recommender on CrewAI sequential YAML
- [x] Frontend and backend share the run document; kickoff is non-streaming; status is polled
- [x] Secrets are environment variable names only
- [x] ATS, messaging, analytics, LinkedIn cookie login, and multi-run scale are Future Work
- [x] Resolved `AAMAD_TARGET_RUNTIME` recorded in Audit

### PRD traceability

| PRD | Architecture |
| --- | --- |
| F1 Submit job requirements | `POST /api/runs`, recruiter form |
| F2 Candidate search | `research_candidates`, source labels, `source_elapsed_ms` |
| F3 Automated evaluation | `evaluate_candidates`, subset guardrail |
| F4 Ranked recommendations | `recommend_candidates`, accept/discard, hiring-manager GET |
| F5 Recruiter satisfaction | `POST /api/runs/{id}/satisfaction` |
| F6 Job posting intake | `POST /api/postings/preview` or pasted text into F1 fields |
| Out of scope: ATS, messaging, analytics | No clients, no routes, no nav |

## Sources

- `project-context/1.define/prd.md` (scope, crew, F1–F6, metrics, UX, security, open questions). Read 2026-11-05.
- `project-context/1.define/mrd.md` (CrewAI example behavior, LinkedIn-cookie disclaimer, NYC Local Law 144, EU AI Act Service Desk employment note). Read 2026-11-05.
- `.cursor/templates/sad-template.md`
- `.cursor/agents/system-arch.md`
- `.cursor/rules/adapter-crewai.mdc`
- `.cursor/rules/adapter-registry.mdc` (unset `AAMAD_TARGET_RUNTIME` defaults to `crewai`)
- `.cursor/rules/epics-index.mdc`
- CrewAI recruitment example and process docs, as cited in the PRD Sources section.
- No user stories were available.

## Assumptions

- `AAMAD_TARGET_RUNTIME` is unset and `aamad.config.yml` is absent. This SAD resolves `crewai`, matching the PRD, the adapter registry default, and the operator request to record that value. `aamad.config.example.yml` was not loaded.
- FastAPI, static HTML/CSS/JS, localhost port 8000, polling, file-per-run storage, `max_rpm` 10, and the character caps are architecture defaults where the PRD is silent. They are not new product features.
- `OPENAI_API_KEY` and `OPENAI_MODEL_NAME` are the env names for the example’s GPT-4o path. A different provider changes the names in `setup.md` and does not change the crew.
- F6 pasted text is in the recruiter form. F6 URL fetch is specified so integration can build it, and it may still be dropped for the first demo (PRD open question).
- `backend/runs/` lives until someone deletes it. That is a storage default, not a retention decision.
- The optional CLI is out of the first Build slice. The two pages satisfy the PRD.
- `@project.mgr` skeleton work can be done by `@backend.eng` if the operator does not add the project-manager persona.
- One process may update `run.json` from the crew thread and from accept/discard. The status machine in Section 4 is the rule those writers follow. A database is not introduced to solve that.
- Model temperature and max tokens are Build audit fields. This SAD does not pick them.

## Open Questions

- Carried from the PRD: time-to-source minute target, match-accuracy percentage and who labels it, satisfaction average, pasted-lead demo without search, whether F6 URL fetch is in Module 06, whether `@project.mgr` and `@security.eng` are in this mini-project, model provider and spend cap, how long run files may be kept, whether any ranking will be used for NYC or EU employment decisions, and whether a required degree may outweigh skills.
- Should the hiring-manager page list run ids, or only open a `run_id` the recruiter copies? This SAD uses the query string so no second index is required.
- Is `max_rpm` 10 acceptable until a spend cap exists?
- If the process crashes mid-run, is a leftover `researching` file enough, or must startup mark stale runs `failed`? This SAD chooses the second behavior and wants confirmation.

## Audit

- **Timestamp**: 2026-11-05T20:47:00-08:00
- **Persona id**: `system-arch`
- **Action**: `create-sad`
- **AAMAD_TARGET_RUNTIME**: `crewai`
- **Runtime warning**: the environment variable was unset and `aamad.config.yml` was not present. Resolved to `crewai` by `.cursor/rules/adapter-registry.mdc`, the PRD Selected Runtime, and the operator instruction to record `crewai`.
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed and were not set by the operator. No crew was executed.
- **Inputs read**: `project-context/1.define/prd.md`, `project-context/1.define/mrd.md` (via the PRD citations and prior Define work), `.cursor/templates/sad-template.md`, `.cursor/agents/system-arch.md`, `.cursor/rules/adapter-crewai.mdc`. No user stories exist.
- **Prompt Trace**: Operator asked `@system.arch` to review the PRD, follow the SAD template, design the Researcher, Evaluator, and Recommender CrewAI crew, define the minimal frontend, backend API, and integration points, record `AAMAD_TARGET_RUNTIME=crewai` in Audit, include Sources, Assumptions, Open Questions, Audit, and MVP security considerations, and save `project-context/1.define/sad.md` for review before code. System-prompt text is omitted.
- **Output path**: `project-context/1.define/sad.md`
- **Handoff**: Ready for review. No application code, pipeline, or third-party integration was added.
