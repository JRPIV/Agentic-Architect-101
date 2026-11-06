# Recruitment Assistant

A mini-project that helps one recruiter turn a job requisition into a sourced shortlist, a requirement-by-requirement evaluation, and a ranked recommendation a hiring manager can read.

The product is specified in [`project-context/1.define/prd.md`](project-context/1.define/prd.md). Market context is in [`project-context/1.define/mrd.md`](project-context/1.define/mrd.md). The use case follows the [CrewAI recruitment example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/recruitment), reduced to three agents. This repository is in the Define phase: the requirements exist, and the application crew is not implemented yet.

Development uses the AAMAD framework (0.7.5). Persona definitions for Cursor live in [`.cursor/agents/`](.cursor/agents/) and are summarized in [`AGENTS.md`](AGENTS.md).

## Project overview and description

A recruiter submits one requisition (title, description, responsibilities, requirements, preferred qualifications, and perks). Three agents run in order:

1. **Researcher** sources candidates from leads the recruiter pastes and, when a search key is configured, from permitted public web results.
2. **Evaluator** scores only those candidates against the submitted job criteria.
3. **Recommender** orders them and writes the ranking the hiring manager reads.

The recruiter operates the run, reviews the draft, and accepts or discards it. The hiring manager reads the accepted ranking. People still decide whom to contact, and they do that outside this product.

The selected application runtime in the PRD is CrewAI (`AAMAD_TARGET_RUNTIME` is unset; the adapter default and the PRD both resolve to `crewai`). There is no `aamad.config.yml` yet. [`aamad.config.example.yml`](aamad.config.example.yml) is a schema sample and is not loaded.

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
- **Job-posting intake (optional).** A posting URL or pasted posting text can fill the same requirement fields. The path is read-only. Pasted requirements are enough if this option is not built.

### Not in this mini-project

- Full ATS integration (no system of record, writeback, or pipeline sync).
- Candidate communication automation (no outreach drafts, email, InMail, or scheduling).
- Advanced analytics (no funnels, time-to-fill warehouse, or multi-requisition dashboards). The single-run ranking is the only report.
- The example’s LinkedIn session-cookie / Selenium login. That upstream README limits the cookie tool to a demonstration.

## Application architecture overview

The application crew is sequential CrewAI. Delegation is off, memory is off, and each agent is capped at 12 iterations. Task order is `research_candidates`, then `evaluate_candidates`, then `recommend_candidates`. The Recommender receives the first two outputs as context. Agent and task YAML are part of Module 06; they are not in the tree yet.

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

Planned integration, once Build starts:

- A model provider key in an environment variable. The upstream example defaults to GPT-4o. This PRD does not lock the provider.
- Optional search and page-reader keys. The upstream example uses `SerperDevTool` and `ScrapeWebsiteTool`.
- Optional read of one job posting into the requirement fields.
- Run output and the satisfaction score can be files. A database is not required.
- One local process or one service. The System Architect chooses that in the SAD.
- Logs record task boundaries, tool names, Researcher elapsed time, and errors. They omit secrets. `LI_AT` is not a supported variable.

The recruiter UI (requirements, status, ranking, accept/discard, satisfaction) and the hiring-manager view of an accepted ranking are frontend work. They are specified in the PRD and not built.

## Getting started

You can read and review the Define artifacts today. You cannot run the assistant yet. There is no crew package, no UI, and no `.env.example`.

### Prerequisites

- Git
- Python 3.14 is what this workspace used to install AAMAD. A current Python 3 is enough to read the docs
- AAMAD in the `>=0.7.5,<0.8` range if you want the validator:

```bash
python3 -m pip install "aamad>=0.7.5,<0.8"
```

`pip` may be absent from `PATH`. `python3 -m pip` matches the install used for this repo.

### Open the project

```bash
cd recruitment-assistant
```

Read, in this order:

1. This README
2. [`project-context/1.define/prd.md`](project-context/1.define/prd.md)
3. [`project-context/1.define/mrd.md`](project-context/1.define/mrd.md)
4. [`AGENTS.md`](AGENTS.md) and [`CHECKLIST.md`](CHECKLIST.md)

### Check Define artifacts

```bash
aamad validate
```

The Define gate also expects `project-context/1.define/sad.md`. That file is the System Architect’s next deliverable, so validation reports it missing until Module 06 starts. `mrd.md` and `prd.md` are present and include Sources, Assumptions, Open Questions, and Audit.

### Runtime keys (later, not now)

When the crew exists, Build will add `.env.example` with names only. Expected names from the PRD are a model API key and, only if those options are turned on, a search key. Do not add a LinkedIn `li_at` cookie. Do not commit secret values.

## Project structure

```text
recruitment-assistant/
├── README.md                          # this file
├── AGENTS.md                          # AAMAD persona index
├── CHECKLIST.md                       # phase checklist from aamad init
├── aamad.config.example.yml           # sample config; not loaded
├── .cursor/
│   ├── agents/                        # Cursor personas (@product-mgr, @system.arch, …)
│   ├── rules/                         # AAMAD core, workflows, runtime adapters
│   ├── templates/                     # MRD, PRD, SAD, SFS, story, user-guide templates
│   └── prompts/
├── project-context/
│   ├── 1.define/
│   │   ├── mrd.md                     # market research
│   │   └── prd.md                     # product requirements (authoritative scope)
│   ├── 2.build/                       # empty until Module 06 (setup, crew, UI, QA notes)
│   └── 3.deliver/                     # empty until Module 07 (deploy and user guide)
```

There is no `src/`, `config/agents.yaml`, or frontend app yet.

## Next steps for contributors

Work from the PRD. Do not expand into ATS sync, candidate messaging, or analytics dashboards.

1. **Resolve open questions that block design.** The list is at the end of the PRD. The ones that change Build are: whether a pasted-lead demo is enough without a search API, whether optional job-posting intake is in Module 06, which model and spend cap to use, and whether `@project.mgr` and `@security.eng` join this mini-project. They are in the AAMAD epic index and are not in the stakeholder module map.
2. **Module 06, architecture.** `@system.arch` writes `project-context/1.define/sad.md` (and any SFS) for the three-agent sequential crew, the draft/accept gate, and the optional posting read.
3. **Module 06, implementation.** After the SAD:
   - `@backend.eng` implements the CrewAI crew (`researcher`, `evaluator`, `recommender`) and the run output.
   - `@frontend.eng` builds the recruiter page and the hiring-manager view of an accepted ranking.
   - `@integration.eng` wires the UI to the crew and, if in scope, the posting read.
   - `@qa.eng` checks search, evaluation, ranking, the three metrics, and the out-of-scope boundaries.
4. **Module 07, deliver.** `@devops.eng` writes deploy, CI, runbook, and user-guide notes after QA. A live deploy is not authorized by the PRD.
5. **Keep artifacts traceable.** New product behavior belongs in the PRD first. Record assumptions and open questions rather than inventing scope in code or chat.

Reference behavior for sourcing shape and the LinkedIn-cookie warning: [crews/recruitment](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/recruitment). This project’s crew stops at Researcher, Evaluator, and Recommender.
