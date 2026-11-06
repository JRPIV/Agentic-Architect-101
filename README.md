# Recruitment Assistant

A mini-project that helps one recruiter turn a job requisition into a sourced shortlist, a requirement-by-requirement evaluation, and a ranked recommendation a hiring manager can read.

The product is specified in [`project-context/1.define/prd.md`](project-context/1.define/prd.md). Market context is in [`project-context/1.define/mrd.md`](project-context/1.define/mrd.md). The architecture is in [`project-context/1.define/sad.md`](project-context/1.define/sad.md). The use case follows the [CrewAI recruitment example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/recruitment), reduced to three agents.

**Current status:** Local delivery and simulated validation complete. Successful live CrewAI execution remains unverified because API credits were unavailable.

FastAPI serves the recruiter page, the hiring-manager page, and the API on `127.0.0.1:8000`. Pytest reports 17 passed. Those tests stub the crew. QA's browser pass of draft, accept, discard, satisfaction, and the hiring-manager view used synthetic candidates. Neither the tests nor that browser pass proves live model behavior. A live crew call on 2026-11-05 reached OpenAI and failed during research with HTTP 429 `credit_balance_exhausted`. That run was not accepted, and it will not be retried. `security.md` is still absent and remains an accepted gap for this localhost exercise. The runbook is [`project-context/3.deliver/deploy.md`](project-context/3.deliver/deploy.md). The execution record is [`project-context/3.deliver/execution-results.md`](project-context/3.deliver/execution-results.md). The verified setup is [`project-context/2.build/setup.md`](project-context/2.build/setup.md).

Development uses the AAMAD framework (0.7.5). Persona definitions for Cursor live in [`.cursor/agents/`](.cursor/agents/) and are summarized in [`AGENTS.md`](AGENTS.md).

## Project overview and description

A recruiter submits one requisition (title, description, responsibilities, requirements, preferred qualifications, and perks). Three agents run in order:

1. **Researcher** sources candidates from leads the recruiter pastes and, when a search key is configured, from permitted public web results.
2. **Evaluator** scores only those candidates against the submitted job criteria.
3. **Recommender** orders them and writes the ranking the hiring manager reads.

The recruiter operates the run, reviews the draft, and accepts or discards it. The hiring manager reads the accepted ranking. People still decide whom to contact, and they do that outside this product.

The application runtime is CrewAI. `AAMAD_TARGET_RUNTIME` resolves to `crewai` from the PRD, the SAD, and `.env.example`. There is no `aamad.config.yml`. [`aamad.config.example.yml`](aamad.config.example.yml) is a schema sample and is not loaded. The installed crew is CrewAI 1.15.36 on Python 3.13.

### Who it is for

| Persona | Need | What they do here |
| --- | --- | --- |
| Recruiter (primary) | Find qualified candidates quickly for one open role | Submit requirements, start the run, review sources and evaluations, rate the run, hand the ranking to the hiring manager |
| Hiring manager (secondary) | Ranked candidate recommendations | Read the accepted list, scores, and gaps. They do not start the crew |

### Success metrics

The PRD defines three goals. Numeric thresholds are still open.

- **Time to source candidates.** Elapsed time from submit until the Researcher returns the candidate list. A completed run records that time.
- **Candidate match accuracy.** Every ranked person comes from the sourced list, and every recommendation states which requirements are met and which are missing.
- **Recruiter satisfaction.** After the ranking is shown, the recruiter saves a 1–5 score with the run.

## Problem statement and value proposition

Recruiters still build a first shortlist by hand, and hiring managers wait on that list before they can compare people. LinkedIn’s Future of Recruiting 2024 survey found 27% of talent professionals using or experimenting with generative AI. Employ’s 2024 Recruiter Nation Report found candidate matching (55%) and intelligent sourcing (44%) among the leading reported AI uses. Citations and the conflicting market-size figures are in the MRD. Those figures are context, not a revenue target for this repo.

The value of this assistant is a reviewable shortlist in one run: sourced people with URLs or an operator-supplied label, evaluations tied to the requisition, and a ranking the recruiter can hand over. Search, evaluation, and ranking stay in separate stages so a weak reason is visible.

This is an operator tool for a mini-project, not a commercial launch.

## Key features

- **Candidate search from job requirements.** Up to 10 candidates. Pasted leads are labeled operator-supplied. Search-added leads include the URL that was read. If nothing was pasted and search finds no one, the research stage fails and does not invent people.
- **Automated candidate evaluation.** Each sourced candidate gets a 1–5 score plus the requirements met and the requirements missing. Missing evidence scores 1.
- **Ranked recommendations.** Highest score first. Ties keep the Researcher order. The list stays a draft until the recruiter accepts it. Accept records a timestamp and a recruiter label.
- **Recruiter satisfaction.** A 1–5 score stored with the run after a draft exists.
- **Job-posting intake (optional).** A posting URL or pasted posting text can fill the same requirement fields. The path is read-only and does not start the crew. Pasted requirements are enough on their own.

### Not in this mini-project

- Full ATS integration (no system of record, writeback, or pipeline sync).
- Candidate communication automation (no outreach drafts, email, InMail, or scheduling).
- Advanced analytics (no funnels, time-to-fill warehouse, or multi-requisition dashboards). The single-run ranking is the only report.
- The example’s LinkedIn session-cookie / Selenium login. That upstream README limits the cookie tool to a demonstration.

## Application architecture overview

The application crew is sequential CrewAI. Delegation is off, memory is off, and each agent is capped at 12 iterations. Task order is `research_candidates`, then `evaluate_candidates`, then `recommend_candidates`. The Recommender receives the first two outputs as context. Agent and task YAML are in [`backend/config/agents.yaml`](backend/config/agents.yaml) and [`backend/config/tasks.yaml`](backend/config/tasks.yaml).

```text
Job requirements
        |
        v
+-------------------+
| Researcher        |  sources candidates (pasted leads and optional public web)
+-------------------+
        |
        v
+-------------------+
| Evaluator         |  scores only those candidates against the job criteria
+-------------------+
        |
        v
+-------------------+
| Recommender       |  ranked list for the recruiter and the hiring manager
+-------------------+
        |
        v
Draft ranking -- recruiter accepts or discards --> Hiring manager reads accepted ranking
```

| Agent | Role | Tools | Output |
| --- | --- | --- | --- |
| `researcher` | Candidate Researcher | Optional web search and page reader when a search key is set. No LinkedIn session tool | Sourced candidates with a source label or URL, plus elapsed time |
| `evaluator` | Candidate Evaluator | None. Scoring stays on evidence already collected | 1–5 score, met requirements, missing requirements |
| `recommender` | Candidate Recommender | None | Ranked recommendation. Status starts as `draft` |

What the local process does:

- The model name comes from `OPENAI_MODEL` in the environment, default `gpt-4o`. The key is `OPENAI_API_KEY`. The PRD does not lock a different provider.
- Optional search uses `SerperDevTool` and `ScrapeWebsiteTool` on the Researcher only when `SERPER_API_KEY` is set. With that key empty, pasted leads are the only source.
- Optional posting preview reads one posting URL or pasted posting text into the requirement fields. It does not create a run and it does not write back.
- Each run is a file under `backend/runs/{run_id}/`. A database is not used.
- One FastAPI process serves the pages and the API on `127.0.0.1:8000`.
- Logs record task boundaries, tool names, Researcher elapsed time, and errors. They omit secrets. `LI_AT` is not a supported variable.

The recruiter page (`/`) and the hiring-manager page (`/hiring-manager`) are the interface. The recruiter submits requirements, watches the stage, and accepts or discards the draft. The hiring manager reads an accepted ranking and has no run controls.

## Getting started

### Prerequisites

- Git
- Python 3.13. CrewAI 1.15.36 requires Python `>=3.10,<3.14`. This workspace's `.venv` is Python 3.13.18. A default `python3` of 3.14 cannot install this backend
- AAMAD in the `>=0.7.5,<0.8` range only if you want `aamad validate`:

```bash
python3 -m pip install "aamad>=0.7.5,<0.8"
```

### Install and run

From this directory. This machine's default `python3` is 3.14, which cannot install CrewAI 1.15.36. The validated interpreter is Python 3.13.18 through uv:

```bash
uv python find 3.13 --system
uv venv --python 3.13 .venv
uv pip install -r backend/requirements.txt --python .venv/bin/python
cp .env.example .env
```

Skip the `uv venv` command when `.venv` is already present. This workspace's `.venv` is Python 3.13.18. Copy `.env.example` only when `.env` is missing. Edit `.env` and set `OPENAI_API_KEY` before a live crew run. Leave `SERPER_API_KEY` empty to use pasted leads only. Leave `CREWAI_TRACING_ENABLED` false. Do not add a LinkedIn `li_at` cookie. Do not commit secret values. CrewAI loads `.env` from this directory when the crew module is imported.

Start the app on localhost only:

```bash
.venv/bin/python -m backend
```

That command binds `127.0.0.1:8000`. The same bind is what `backend/__main__.py` passes to Uvicorn.

Open:

- Recruiter: `http://127.0.0.1:8000/`
- Hiring manager: `http://127.0.0.1:8000/hiring-manager`
- Health: `http://127.0.0.1:8000/health`

Do not bind `0.0.0.0`. Opening the HTML files from disk does not reach `/api`.

A run with a title, requirements, and pasted leads calls the model. A run with empty pasted leads and an empty `SERPER_API_KEY` fails at research and does not call the model. The ranking stays a draft until the recruiter accepts it.

### Tests

```bash
.venv/bin/python -m pytest
```

The automated tests stub the crew. They do not call a model. The latest QA record is [`project-context/2.build/qa.md`](project-context/2.build/qa.md). The latest execution record, including the failed live call, is [`project-context/3.deliver/execution-results.md`](project-context/3.deliver/execution-results.md).

### Read the project

1. This README
2. [`project-context/1.define/prd.md`](project-context/1.define/prd.md)
3. [`project-context/1.define/sad.md`](project-context/1.define/sad.md)
4. [`project-context/2.build/qa.md`](project-context/2.build/qa.md)
5. [`project-context/3.deliver/deploy.md`](project-context/3.deliver/deploy.md)
6. [`project-context/3.deliver/execution-results.md`](project-context/3.deliver/execution-results.md)
7. [`LESSONS.md`](LESSONS.md)
8. [`AGENTS.md`](AGENTS.md) and [`CHECKLIST.md`](CHECKLIST.md)

## Project structure

```text
recruitment-assistant/
├── README.md                          # this file
├── LESSONS.md                         # Define, Build, Deliver, and review notes
├── AGENTS.md                          # AAMAD persona index
├── CHECKLIST.md                       # phase checklist from aamad init
├── .env.example                       # variable names only
├── aamad.config.example.yml           # sample config; not loaded
├── Dockerfile                         # untested package of the same process
├── backend/                           # CrewAI crew, FastAPI, tests
│   ├── config/agents.yaml
│   ├── config/tasks.yaml
│   └── app.py                         # API plus the two pages
├── frontend/                          # recruiter and hiring-manager pages
├── .cursor/
│   ├── agents/                        # Cursor personas
│   ├── rules/                         # AAMAD core, workflows, runtime adapters
│   └── templates/
└── project-context/
    ├── 1.define/                      # mrd.md, prd.md, sad.md
    ├── 2.build/                       # setup, backend, frontend, integration, qa notes
    └── 3.deliver/                     # deploy.md, execution-results.md
```

## Next steps for contributors

Work from the PRD. Do not expand into ATS sync, candidate messaging, or analytics dashboards.

1. **Local delivery and simulated validation are complete.** The runbook, setup note, metadata logs, and execution record are in place. The PRD does not authorize a live deploy. CI and the optional user guide were left out of this closeout.
2. **Successful live CrewAI execution remains unverified because API credits were unavailable.** The 2026-11-05 pasted-lead run, with search off, returned HTTP 429 `credit_balance_exhausted` and was not accepted. This exercise will not purchase credits or retry that call. Search stays off unless `SERPER_API_KEY` is set on purpose.
3. **Security assessment is still a gap.** `project-context/2.build/security.md` was not written. That absence is accepted for this localhost exercise only.
4. **Keep artifacts traceable.** New product behavior belongs in the PRD first. Record assumptions and open questions rather than inventing scope in code or chat.

Reference behavior for sourcing shape and the LinkedIn-cookie warning: [crews/recruitment](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/recruitment). This project’s crew stops at Researcher, Evaluator, and Recommender.
