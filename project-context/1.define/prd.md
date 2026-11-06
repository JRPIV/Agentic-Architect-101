# Product Requirements Document: Recruitment Assistant

## Document Control

**Deep Research Report / MRD**: `project-context/1.define/mrd.md`  
**System Description**: Not produced. The operator ordered `*create-mrd` then `*create-prd`, then revised this PRD with the mini-project scope below.  
**System Concept**: A recruitment assistant that takes job requirements and returns sourced candidates, an evaluation of those candidates against the requirements, and a ranked recommendation the hiring manager can read.  
**Selected Runtime**: `crewai`  
**Revision**: Stakeholder scope in this revision replaces the earlier four-agent crew (researcher, matcher, communicator, reporter). The application crew is Researcher, Evaluator, and Recommender. Candidate communication is out of scope.

## Product Overview

### High-level description

The recruitment assistant helps a recruiter fill one requisition. The recruiter supplies job requirements. A three-agent crew then searches for candidates, evaluates each candidate against those requirements, and produces a ranked recommendation list. The hiring manager reads that ranking. The product is a mini-project based on the CrewAI recruitment example (`crewAIInc/crewAI-examples`, `crews/recruitment`): same sourcing-and-evaluation idea, a smaller crew, and a hard stop before messaging candidates or replacing an ATS.

The recruiter can paste requirements or, optionally, point the run at a job posting. Optional posting intake reads a posting into the same requirements input. It is not an ATS connection. The example’s LinkedIn session-cookie tool stays out of the product. The example README limits that tool to a Selenium demonstration.

### Core value proposition

Recruiters get a sourced, explained shortlist in one run instead of assembling it by hand. Hiring managers get a ranked list with the requirement-level reasons already attached. The value is speed to a reviewable shortlist, a visible match between person and job criteria, and a result the recruiter is willing to hand to a hiring manager. The assistant does the search, the evaluation, and the ranking. People still decide who is contacted, and they do that outside this product.

## Goals and Success Metrics

These three outcomes are the mini-project goals. Numeric thresholds were not supplied; measurement is defined here, and target numbers sit in Open Questions.

### Time to source candidates

- **Goal**: Shorten the time from “job requirements are known” to “a candidate list exists.”
- **Metric**: Elapsed time from requisition submit to the Researcher stage returning its candidate list, shown on the run.
- **Mini-project success**: One requisition produces that list in a single run, and the elapsed time is recorded. A pass/fail minute cap is not set.

### Candidate match accuracy

- **Goal**: Recommended people fit the job requirements that were submitted.
- **Metric**: For each ranked candidate, the Evaluator records which submitted requirements are met and which are missing. Accuracy for this mini-project means every ranked person came from the Researcher list, and every recommendation includes that requirement-level evaluation.
- **Mini-project success**: A scripted review of the sample requisition finds no ranked person who is absent from the sourced list, and no recommendation that omits the met/missing requirements. A percent-correct target against a labeled candidate dataset was not provided.

### Recruiter satisfaction

- **Goal**: The recruiter judges the run useful for finding qualified candidates quickly.
- **Metric**: After the ranked list is shown, the recruiter records a 1–5 satisfaction score and may add a short comment. The score is stored with the run.
- **Mini-project success**: The rating control is present and the score persists with the run. A minimum average score is not set.

## User Personas

### Primary: Recruiter

- Needs to find qualified candidates quickly for one open role.
- Submits job requirements, starts the run, and reviews the sourced list and the evaluations.
- Hands the ranked recommendations to the hiring manager.
- Does not use this product to email, message, or schedule candidates.

### Secondary: Hiring Manager

- Needs ranked candidate recommendations for the role they are hiring.
- Reads the ordered list, the match reasons, and the gaps.
- Does not configure search and does not run the crew. The recruiter operates the assistant.

## Core Features

### Candidate search based on job requirements

The Researcher searches and sources candidates from the submitted requirements. Leads the recruiter pastes are included and labeled operator-supplied. When a search key is configured, public web results may add leads, each with the URL that was read. The stage returns at most 10 candidates. Fewer is acceptable when fewer sourced leads exist. Zero sourced leads and zero pasted leads fails the stage. The stage does not invent people.

### Automated candidate evaluation

The Evaluator judges only candidates the Researcher returned. Each evaluation names the job requirements that are met and the requirements that are missing, plus a 1–5 score. A candidate with no usable evidence is scored 1 and the evaluation says the evidence is missing.

### Ranked candidate recommendations

The Recommender orders candidates by score, highest first, and presents that order to the recruiter and the hiring manager. Each row keeps the source, the score, and the met/missing requirements. Ties keep the Researcher list order. The list is a draft until the recruiter accepts it. Acceptance records the time and a recruiter label. Discard keeps the draft readable and unaccepted.

### Integration with job posting systems (optional for mini-project)

Optional input: a job-posting URL or pasted posting text. The run turns that posting into the same job-requirements fields used by search. This optional path is read-only. It does not create postings, update postings, or write candidates back to a posting system. If the optional path is not built, pasted requirements remain a complete way to run the crew.

## Application Crew Definition

Runtime is CrewAI, sequential process, `allow_delegation=false`, `memory=false`, `max_iter <= 12`, `max_retry_limit >= 2`. Agent and task definitions live in YAML. The Recommender task receives the Researcher and Evaluator outputs as context. The example’s communicator and its outreach task are not in this crew.

### Researcher Agent

- **agent**: `researcher`
- **role**: Candidate Researcher
- **goal**: Search and source candidates for the submitted job requirements.
- **backstory**: Finds plausible people from operator-supplied leads and, when enabled, permitted public web results. Records where each candidate came from. Does not invent people, employers, or contact details.
- **tools**: Optional web search and page reader when a search key is configured. No LinkedIn session tool.
- **runtime notes**: If search is off and no leads were pasted, the task fails clearly and does not fabricate a list.

### Evaluator Agent

- **agent**: `evaluator`
- **role**: Candidate Evaluator
- **goal**: Evaluate each sourced candidate against the job criteria.
- **backstory**: Scores only people present in the Researcher output. Ties every score to requirements in the requisition. Preferred qualifications cannot by themselves outweigh missing required skills.
- **tools**: None. Evaluation stays on the evidence already collected.
- **runtime notes**: Integer score 1–5, met requirements, missing requirements.

### Recommender Agent

- **agent**: `recommender`
- **role**: Candidate Recommender
- **goal**: Provide ranked candidate recommendations for the recruiter and the hiring manager.
- **backstory**: Orders the evaluated candidates and writes a short recommendation the hiring manager can read without opening agent logs. Does not draft or send candidate messages.
- **tools**: None.
- **runtime notes**: Context is the Researcher and Evaluator outputs. The recommendation stays `draft` until the recruiter accepts it.

## Development Crew Mapping (Define + upcoming Build)

| Phase | Module | Persona | Owns |
| --- | --- | --- | --- |
| Define | — | @product-mgr | This PRD and `project-context/1.define/mrd.md`. No application code. |
| Build | Module 06 | @system.arch | SAD and SFS from this PRD: three-agent sequential crew, optional posting read, no messaging. |
| Build | Module 06 | @backend.eng | CrewAI crew (`researcher`, `evaluator`, `recommender`), tasks, and run output. |
| Build | Module 06 | @frontend.eng | Recruiter UI for requirements, run status, ranked recommendations, accept/discard, and the satisfaction score. A hiring-manager view of the accepted ranking. |
| Build | Module 06 | @integration.eng | Wire the UI to the crew. Optional job-posting read if that option is in the build. |
| Build | Module 06 | @qa.eng | Verify search, evaluation, ranking, the three success metrics, and the out-of-scope boundaries. |
| Deliver | Module 07 | @devops.eng | Deploy definition, CI scaffolding, runbook, and user guide after QA. |

Module 06 is the Build slice for this mini-project. Module 07 is Deliver. AAMAD’s epic index also names @project.mgr (setup) and @security.eng (security assessment). They are not in the stakeholder module map above. See Open Questions.

## Out of Scope (for this mini-project)

- **Full ATS integration.** No system of record, no candidate writeback, no pipeline stages, no two-way sync. The optional job-posting read is not an ATS.
- **Candidate communication automation.** No outreach drafts, no email, no InMail, no chatbots, and no scheduling. The example’s communicator agent is not built.
- **Advanced analytics and reporting.** No funnel dashboards, no time-to-fill warehouse, no quality-of-hire model, no multi-requisition analytics. The ranked recommendation for one run is the only report.

Also out of this mini-project, carried forward from the MRD constraints: LinkedIn session-cookie or Selenium login, crew training mode, multi-user SSO, a bias-audit program, and a commercial launch.

## 1. Executive Summary

### Problem Statement

Recruiters still build a first shortlist by hand, and hiring managers wait on that list before they can compare people. LinkedIn’s Future of Recruiting 2024 survey found 27% of talent professionals using or experimenting with generative AI. Employ’s 2024 Recruiter Nation Report found candidate matching (55%) and intelligent sourcing (44%) among the leading AI uses. This mini-project serves one recruiter and the hiring manager for a single requisition. Market totals in the MRD (Mordor’s narrower AI recruitment market versus QY Research’s wider tool market) are context, not a revenue target.

### Solution Overview

Three agents run in order: Researcher, Evaluator, Recommender. The recruiter gets sourced candidates and evaluations. The hiring manager gets the ranked recommendations. Success is the three metrics in Goals and Success Metrics: time to source, match accuracy, and recruiter satisfaction.

### Strategic Rationale

Separating search, evaluation, and ranking keeps each handoff inspectable. That split follows the CrewAI recruitment example’s sequential crew and the CrewAI adapter’s MVP default, with the communicator stage removed because communication automation is out of scope. The mini-project is an operator tool, not a priced product.

## 2. Market Context and User Analysis

Personas are defined under User Personas. Market size, geography, and competitors are in `project-context/1.define/mrd.md`.

- Mordor Intelligence: AI recruitment market USD 596.16 million (2025) to USD 920.91 million (2031), 7.52% CAGR for 2026–2031. North America was 41.62% of 2025 revenue.
- QY Research (published 2026-03-06): AI recruiting tools US$2,794 million (2025) to US$8,662 million (2032), 17.8% CAGR for 2026–2032.
- Alternatives recruiters use today include manual search plus a spreadsheet, Gem’s broader recruiting platform, and natural-language sourcing such as SeekOut Assist and Eightfold Recruiter Copilot (as described by SHRM). This mini-project fills the gap of one explainable, ranked shortlist. It does not replace those platforms.
- Adoption depends on sourced people being real and on evaluations citing the job requirements. A ranking the recruiter will not show a hiring manager fails the satisfaction goal.

## 3. Technical Requirements and Architecture

### Runtime and Agent Specifications

Specified under Application Crew Definition. Task order is `research_candidates`, then `evaluate_candidates`, then `recommend_candidates`. Report context is the first two tasks only.

### Integration Requirements

- Model provider API key in an environment variable. The example defaults to GPT-4o. Build selects the provider. This PRD does not make that vendor the product definition.
- Optional search API and page reader, off unless keys are present. The example uses `SerperDevTool` and `ScrapeWebsiteTool`.
- Optional job-posting read: one URL fetch or pasted posting text into job-requirements fields.
- No database required. The run’s recommendation and satisfaction score can be files.
- No login service for the mini-project. The recruiter is whoever can start the process.

### Infrastructure Specifications

- One local process or one single service, chosen in the SAD during Module 06.
- Logs record task start, task end, tool names, elapsed time for the Researcher stage, and errors. Logs omit API keys and cookies. Build logs go under `project-context/2.build/logs`.
- `.env.example` lists variable names only. `LI_AT` is not a supported variable.
- One requisition per run. The run ends in a draft recommendation or a visible failure. A 15-minute `max_execution_time` guard is an engineering cap, not the time-to-source target.

## 4. Functional Requirements

### Core Features (Priority P0)

**F1. Submit job requirements**

As a recruiter, I submit one requisition so the crew can search.

Acceptance criteria:

- Fields cover title, description, responsibilities, requirements, preferred qualifications, and perks and benefits, matching the example input in `main.py`.
- A missing title or a missing requirements field blocks the run and names the field.
- The submitted text is stored with the run.

**F2. Candidate search**

As a recruiter, I receive sourced candidates for those requirements.

Acceptance criteria:

- Pasted leads are labeled operator-supplied.
- Search-added leads each include a source URL.
- At most 10 candidates. Fewer is allowed. Zero candidates with no pasted leads fails research and does not invent people.
- Email and phone are omitted unless they were in the pasted text or on a cited page.
- The LinkedIn session tool is not callable.
- Elapsed time for this stage is stored for the time-to-source metric.

**F3. Automated evaluation**

As a recruiter, I can read how each sourced candidate meets the job criteria.

Acceptance criteria:

- Every evaluated person appears in the F2 list. The Evaluator adds no one.
- Each candidate has a 1–5 score, met requirements, and missing requirements.
- Missing evidence scores 1 and says the evidence is missing.

**F4. Ranked recommendations**

As a hiring manager, I can read candidates in rank order with the reasons attached.

Acceptance criteria:

- Order is score descending. Ties keep Researcher order.
- Each row includes source, score, met requirements, and missing requirements.
- The recommendation has no outreach text and no send control.
- Status starts as `draft`. Recruiter accept sets `accepted` with a timestamp and a recruiter label. Discard sets `discarded`.
- The hiring manager view shows accepted rankings. Drafts stay on the recruiter view.

**F5. Recruiter satisfaction**

As a recruiter, I can rate the run after I see the ranking.

Acceptance criteria:

- A 1–5 score can be saved with the run after a draft exists.
- The score remains attached to that run.

### Optional (mini-project)

**F6. Job posting intake**

As a recruiter, I can start from a job posting instead of typing every field.

Acceptance criteria:

- A posting URL or pasted posting text fills the F1 fields before the crew starts.
- Failure to read a URL leaves the form editable and does not start the crew with empty requirements.
- Nothing is written back to the posting system.

### Future Features (Priority P2)

- Full ATS integration, candidate messaging, and multi-run analytics (also listed under Out of Scope).
- LinkedIn official APIs or session-cookie automation.
- Multi-user accounts, SSO, and a bias-audit program for NYC Local Law 144 or EU high-risk employment use.
- Crew training (`train` in the example `main.py`).
- A paid or multi-tenant service.

## 5. Non-Functional Requirements

### Performance

- One active run at a time.
- Time to source is measured, not given a numeric SLA in this revision.
- If a task exceeds its iteration cap or the execution guard, the run stops with the stage name and a plain-language reason.

### Security and Compliance

- Secrets stay in environment variables. Artifacts and logs do not contain secret values.
- The product stores the requisition, sourced candidates, source URLs, evaluations, the ranking, accept/discard, and the satisfaction score.
- The ranking states that it supports the recruiter and the hiring manager and that contact decisions happen outside the product.
- NYC Local Law 144 and the EU AI Act Service Desk’s high-risk employment example still apply if scores substantially drive screening. That compliance design is out of this mini-project. See the MRD.
- Candidate communication is not a feature, so the product has no path that emails a candidate.

### Scalability and Reliability

- Scaling beyond one process and one run is deferred.
- A failed tool retries up to `max_retry_limit` (at least 2) and then fails the task. It does not fill the gap with an unsourced candidate.
- Rerunning creates a new draft. It does not mark an older draft accepted.

## 6. User Experience Design

### Interface Requirements

- Recruiter page: requirement fields, optional pasted leads, optional posting URL, Run, stage status, sourced list, evaluations, ranked recommendations, Accept, Discard, and the 1–5 satisfaction score. Elapsed time for sourcing is visible.
- Hiring manager page: the accepted ranked list for a run, with scores and met/missing requirements. No run controls.
- Desktop browser. A CLI that prints the same recommendation is allowed because the example is a CLI. The pages are required so accept, discard, and the satisfaction score are not hand-edited files.
- Status does not depend on color alone.

### Agent Interaction Design

- Status names the active stage: research, evaluation, or recommendation.
- Failures name the stage and the reason.
- Sources sit next to each candidate.
- The recommendation contains no outreach block.

## 7. Success Metrics and KPIs

The product goals are only the three metrics under Goals and Success Metrics.

| Metric | What QA checks |
| --- | --- |
| Time to source candidates | Researcher elapsed time is recorded and shown for a completed run |
| Candidate match accuracy | Every ranked candidate is in the sourced list and has met and missing requirements |
| Recruiter satisfaction | A 1–5 score saves with the run |

Technical checks that support those metrics:

- An unavailable model ends in a visible failure and does not set the ranking to accepted.
- Logs contain task boundaries and the Researcher elapsed time, and they contain no secret values.
- QA maps at least one test to each P0 acceptance criterion.
- Across QA runs, messages sent by the product stay at zero, and analytics views beyond the single-run ranking stay absent.

## 8. Implementation Strategy

### Development Phases

- **Define**: MRD and this PRD, owned by @product-mgr.
- **Module 06 (Build)**: @system.arch, then @backend.eng and @frontend.eng, then @integration.eng, then @qa.eng, as mapped under Development Crew Mapping.
- **Module 07 (Deliver)**: @devops.eng after QA. This PRD does not authorize a live deploy.

### Resource Requirements

- One crew of three agents and two views (recruiter and hiring manager). No hiring plan is implied.
- External spend is the model API and, if search or posting fetch is on, those calls. No budget number was provided. Module 06 records usage per QA run.

### Risk Mitigation

- Invented candidates: F2 and F3 checks in QA.
- LinkedIn cookie flow from the example: the tool is not in the crew.
- Ranking treated as an employment decision: draft until the recruiter accepts; compliance program is out of scope for this mini-project and remains a risk if the ranking is used that way.
- Empty search: pasted leads still complete evaluation and ranking.

## 9. Launch and Go-to-Market Strategy

Not applicable. This is a mini-project, not a commercial launch. No price, channel, or launch date was requested.

## Quality Assurance Checklist

- [x] Requirements traceable to the stakeholder mini-project scope and to `project-context/1.define/mrd.md`
- [x] Application crew is Researcher, Evaluator, and Recommender on the CrewAI adapter
- [x] Success metrics are time to source, match accuracy, and recruiter satisfaction
- [x] Optional job-posting intake is separate from full ATS integration
- [x] Candidate communication automation and advanced analytics are out of scope
- [x] Market sections stay because the MRD exists; go-to-market is N/A

## Sources

- Stakeholder revision, 2026-11-05: product overview, three success metrics, recruiter and hiring-manager personas, four core features, three-agent crew, Module 06 and Module 07 persona map, and the three out-of-scope items.
- `project-context/1.define/mrd.md` (market figures, compliance tests, example behavior, sources S1–S20).
- CrewAI recruitment example, retrieved 2026-11-05:
  - https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/README.md
  - https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/config/agents.yaml
  - https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/config/tasks.yaml
  - https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/main.py
  - https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/crew.py
  - https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/tools/linkedin.py
- CrewAI process documentation: https://docs.crewai.com/concepts/processes
- This project: `.cursor/templates/prd-template.md`, `.cursor/agents/product-mgr.md`, `.cursor/rules/adapter-crewai.mdc`, `.cursor/rules/adapter-registry.mdc`, `.cursor/rules/epics-index.mdc`, `.cursor/rules/development-workflow.mdc`, `aamad.config.example.yml` (not loaded).

Market and compliance citations used by name are Mordor Intelligence, QY Research (2026-03-06), LinkedIn Future of Recruiting 2024, Employ Recruiter Nation Report 2024, Gem 2025 Recruiting Benchmarks, SHRM on SeekOut and Eightfold, NYC DCWP Local Law 144 FAQ, and the EU AI Act Service Desk employment page. URLs and retrieval dates are in the MRD Sources section.

## Assumptions

- The stakeholder revision is authoritative for mini-project scope where it differs from the first PRD draft and from the four-agent example. The example still supplies the requisition shape, the sequential CrewAI process, the sourcing task, and the LinkedIn-cookie warning.
- Researcher maps to the example researcher. Evaluator maps to the example matcher, without that agent’s web tools. Recommender maps to the example reporter and produces the ranking. The example communicator is dropped because candidate communication automation is out of scope.
- “Integration with job posting systems (optional)” means read a posting into job requirements. “Full ATS integration” means writeback, pipeline, and system of record, which is out of scope.
- “Advanced analytics and reporting” means dashboards and cross-run analytics. The single-run ranked recommendation is in scope. It is the Recommender’s output, not an analytics product.
- Numeric targets for the three success metrics were not given. The metrics are in scope. The thresholds are open.
- The 1–5 evaluation score and the 1–5 satisfaction score are separate scales. The 15-minute execution guard is an engineering cap, not the time-to-source goal.
- `AAMAD_TARGET_RUNTIME=crewai` by adapter default. The environment variable was unset. `aamad.config.yml` does not exist and `aamad.config.example.yml` was not loaded. Its `runtime.target: crewai` matches the default.
- @project.mgr and @security.eng are in the framework epic index and were not named in the Module 06 / Module 07 map. This PRD does not assign them work unless a later answer adds them.
- English requisitions, one recruiter operating the run, one hiring manager reading the accepted ranking. No industry vertical was chosen.
- This document does not provide a legal opinion on Local Law 144 or the EU AI Act.

## Open Questions

- What minute target should time-to-source beat for a demo to count as successful?
- What match-accuracy percentage is required, and who labels the correct set?
- What recruiter-satisfaction average is the minimum, and how many ratings are enough?
- Is a demo without a search API acceptable when the recruiter pastes leads?
- Is optional job-posting intake in the Module 06 build, or deferred inside the mini-project?
- Should @project.mgr (setup) and @security.eng run inside Module 06, or stay out of this mini-project?
- Which model provider and spend cap should Module 06 use?
- How long may rankings that contain names and profile URLs stay on disk?
- Will any ranking be used to screen candidates for a New York City job or under the EU AI Act’s employment category?
- Should a required degree outweigh demonstrated skills? The sample requisition lists a bachelor’s degree under preferred qualifications.

## Audit

- **Timestamp**: 2026-11-05T19:22:00-08:00
- **Persona id**: `product-mgr`
- **Action**: `create-prd` (stakeholder revision of `project-context/1.define/prd.md`)
- **AAMAD_TARGET_RUNTIME**: `crewai`
- **Runtime warning**: unset environment variable and missing `aamad.config.yml`. Resolved to `crewai` by `.cursor/rules/adapter-registry.mdc`. Example config was not loaded.
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed and were not set by the operator.
- **Inputs read**: the prior `prd.md`, `project-context/1.define/mrd.md`, the PRD template, the product-manager persona, the CrewAI adapter rule, `epics-index.mdc`, and `development-workflow.mdc`.
- **Prompt Trace**: Operator asked the PRD to include a product overview and value proposition; goals for time to source, match accuracy, and recruiter satisfaction; recruiter and hiring-manager personas; core features for search, evaluation, ranked recommendations, and optional job-posting integration; a Researcher, Evaluator, and Recommender crew; a Define / Module 06 / Module 07 persona map; and an out-of-scope list of full ATS integration, candidate communication automation, and advanced analytics. System-prompt text is omitted.
- **Output path**: `project-context/1.define/prd.md`
- **Handoff**: Module 06 starts with @system.arch using this PRD. User stories were not requested.
