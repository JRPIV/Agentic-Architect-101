# Lessons learned

Recorded lessons cite a project artifact or a command from this Deliver pass. Sections marked **Suggestion for review** are inferences for Joey. They are not findings the artifacts already state.

## Define

The MRD described the upstream four-agent recruitment crew, including a communicator and a LinkedIn session tool. The revised PRD kept Researcher, Evaluator, and Recommender and put messaging, ATS sync, analytics, and the LinkedIn cookie out of scope. That written cut is what later kept the API from growing a send path. Source: `project-context/1.define/mrd.md`, `project-context/1.define/prd.md`.

The three success metrics have definitions and no numeric threshold. QA could not invent a pass/fail minute cap, and this Deliver pass does not add one. The failed live run's `source_elapsed_ms` of 27690 is a failure time, not a score against an unstated target. Source: PRD Open Questions, `project-context/2.build/qa.md`.

The PRD module map assigns `@project.mgr` and `@security.eng` to nobody. Build therefore left `setup.md` and `security.md` unwritten. `security.md` is still absent. `setup.md` was added later from the verified local setup. Source: PRD Development Crew Mapping, `project-context/2.build/qa.md`, `project-context/2.build/setup.md`.

## Build

CrewAI 1.15.36 does not install on this machine's default Python 3.14. The working tree uses the Python 3.13.18 virtualenv. Source: `project-context/2.build/backend.md`, `project-context/3.deliver/deploy.md`.

The integration persona text describes a Next.js chat UI. The PRD and SAD describe two pages and a polled run. The build followed the PRD and SAD. Source: `project-context/2.build/integration.md`.

QA's browser pass of draft, accept, discard, satisfaction, and the hiring-manager view used a stubbed executor and synthetic people. It did not call a model. Source: `project-context/2.build/qa.md`.

## Deliver

A configured `OPENAI_API_KEY` is not evidence that a crew run worked. This pass presented the key, left search off, and sent one synthetic pasted lead. OpenAI returned HTTP 429 `credit_balance_exhausted`. Run `9481a8b0-1e3c-4c9f-8e67-cedbe696e768` is `failed`, with `accepted_at` null. Source: `project-context/3.deliver/execution-results.md`.

Request logs can stay useful without storing the lead. `app.log` recorded method, path, and status for that run and did not contain `sam.rivera@example.test`. The prompt file still contains the synthetic lead, because that file is the prompt record. Source: the same execution record and `backend/trace.py`.

`CREWAI_TELEMETRY_OPT_OUT=true` does not by itself turn off CrewAI execution tracing. CrewAI 1.15.36 reads `CREWAI_TRACING_ENABLED`. This process sets that to `false` when it is unset, after `.env` loads. The server log showed `crewai_tracing=false`. Source: `backend/crew.py`, `.env.example`, the startup line in the execution record.

The Step 1 package includes a `Dockerfile`. `docker` was not used in that step, and this pass did not build the image. The procedure that ran is `.venv/bin/python -m backend` on `127.0.0.1:8000`. Source: `project-context/3.deliver/deploy.md`.

## AAMAD

There is no `aamad.config.yml`. `aamad.config.example.yml` would require a security assessment, a user guide, and unit tests, but that file is a sample and is not loaded. The missing assessment was recorded as an accepted local gap instead of copying the example into place. Source: `aamad.config.example.yml`, deploy.md Assumptions.

Persona outputs disagreed with the product in one place, and the product artifacts won. The integration note says so. Source: `project-context/2.build/integration.md`.

The audits are what keep a simulated pass from being retold as a live pass. QA says the browser smoke did not call a model. This execution file says the live call failed. Source: `project-context/2.build/qa.md`, `project-context/3.deliver/execution-results.md`.

## The architect's three hats

The course names these hats Technical, Experience, and Business. Each item below is tied to an artifact or to the 2026-11-05 execution record.

### Technical

The SAD fixes one process on `127.0.0.1:8000`, a sequential Researcher, Evaluator, and Recommender crew, and a file under `backend/runs/` for each run. The crew cannot set `accepted`. Source: `project-context/1.define/sad.md`, `project-context/2.build/backend.md`.

CrewAI 1.15.36 does not install on this machine's Python 3.14. The verified interpreter is `.venv/bin/python`, Python 3.13.18. Source: `project-context/2.build/setup.md`.

Pytest covers the guardrails, the draft and accept API, and the hiring-manager page markup with a stubbed executor. Those tests do not prove live model behavior. The one live kickoff failed in research with HTTP 429 before the Evaluator ran. Source: `project-context/2.build/qa.md`, `project-context/3.deliver/execution-results.md`.

### Experience

The recruiter page submits a requisition, watches the stage, and accepts or discards a draft. The hiring-manager page has no Run, Accept, or Discard control and shows a ranking only after accept. Source: `project-context/2.build/frontend.md`, `project-context/2.build/qa.md`.

QA's browser pass walked that path with synthetic people and a stubbed executor. It is evidence for the screens, not for a model-written shortlist. The live hiring-manager view of run `9481a8b0-1e3c-4c9f-8e67-cedbe696e768` showed `Status: failed. Stage: research.` and no ranking. Source: `project-context/2.build/qa.md`, `project-context/3.deliver/execution-results.md`.

### Business

The MRD started from a four-agent example that included outreach and a LinkedIn session tool. The PRD kept a mini-project for one recruiter and one hiring manager, and it left ATS sync, candidate messaging, analytics, and that cookie out of scope. Source: `project-context/1.define/mrd.md`, `project-context/1.define/prd.md`.

The three success metrics are defined and have no numeric target, so this exercise does not claim a business result from `source_elapsed_ms` 27690. That number is how long the failed research call ran. Source: PRD Open Questions, `project-context/3.deliver/execution-results.md`.

The operator will not purchase API credits. Local delivery and simulated validation are the completed part of this Tier-0 exercise. Successful live CrewAI execution remains unverified because API credits were unavailable. Source: `project-context/3.deliver/execution-results.md` and the operator decision on 2026-11-06.

## Suggestions for review

- Keep `security.md` as an open gap until `@security.eng` writes it. This localhost exercise is not that assessment.
- CI, the optional user guide, and a container build were left out of this closeout. Do not treat the `Dockerfile` as a tested package.
- Do not read the 17 passing tests as proof that a live model call ranks candidates.

## Sources

- `project-context/1.define/mrd.md`
- `project-context/1.define/prd.md`
- `project-context/1.define/sad.md`
- `project-context/2.build/backend.md`
- `project-context/2.build/integration.md`
- `project-context/2.build/qa.md`
- `project-context/2.build/setup.md`
- `project-context/2.build/frontend.md`
- `project-context/3.deliver/deploy.md`
- `project-context/3.deliver/execution-results.md`
- `aamad.config.example.yml`

## Assumptions

- `AAMAD_TARGET_RUNTIME` resolves to `crewai`. No `aamad.config.yml` is present.
- The 429 text in the execution record is the provider message stored on the run.

## Open Questions

- The PRD still has no numeric targets for time to source, match accuracy, or satisfaction.

## Audit

- **Timestamp**: 2026-11-05T23:00:49-08:00
- **Persona id**: `devops-eng`
- **Action**: lessons for Module 07
- AAMAD_TARGET_RUNTIME: crewai
- **Prompt Trace**: The operator asked for lessons from the project artifacts, covering Define, Build, Deliver, AAMAD, and the architect's three hats, with inferences labeled for review. System-prompt text is omitted.
- **Output path**: `LESSONS.md`

### 2026-11-06T05:59:47-08:00

- **Persona id**: `devops-eng`
- **Action**: replace the hat section with the course names Technical, Experience, and Business
- AAMAD_TARGET_RUNTIME: crewai
- **What changed**: the hat section now uses those names and cites project evidence. The note that `setup.md` was missing now says Build left it unwritten and Deliver added it. No model call was made.
- **Prompt Trace**: The operator named the course hats and said API credits will not be purchased. System-prompt text is omitted.
