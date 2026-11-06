# Market Research Document: Recruitment Assistant

## Research Query

**Primary Focus**: A recruiter-operated, multi-agent recruitment assistant that turns a written job requisition into a sourced shortlist, a scored match report, outreach drafts, and a recruiter-facing recommendation. The workflow is the official CrewAI recruitment example (`crews/recruitment` in `crewAIInc/crewAI-examples`).

**Selected Runtime**: `crewai` (resolved default; see Audit). The runtime is an implementation choice for the generated MVP. It is separate from the AAMAD Define / Build / Deliver method.

**Research date**: 2026-11-05. Figures below are quoted from the cited pages as retrieved that day. Where publishers disagree, both figures are kept and the scope difference is stated.

## Executive Summary

Recruiters already spend the scarce part of hiring on judgment and relationships, while sourcing, first-pass matching, and first-draft outreach remain slow and repetitive. LinkedIn’s Future of Recruiting 2024 survey (1,453 recruiting professionals and 498 hiring managers, October–November 2023, 23 countries) found that 27% of talent professionals were using or experimenting with generative AI, while about six in ten were optimistic. Among users, the most cited benefits were faster job-description writing (57%), automating tasks to free time for more fulfilling work (45%), and easier candidate engagement (35%). Employ’s 2024 Recruiter Nation Report found 63% of recruiters and talent-acquisition decision makers using AI to augment recruiting technology (up from 58% the prior year), with candidate matching the leading use (55%). The product opportunity is a narrow copilot for one requisition, aligned to work recruiters already do, with the recruiter remaining the decision maker.

Published market sizes conflict because they measure different scopes. Mordor Intelligence’s AI recruitment market is USD 596.16 million in 2025, USD 640.99 million in 2026, and USD 920.91 million by 2031 (7.52% CAGR for 2026–2031). QY Research’s broader “AI Recruiting Tool” market is US$2,794 million in 2025, US$3,242 million in 2026, and US$8,662 million by 2032 (17.8% CAGR for 2026–2032). This project should not pick one total addressable market as a revenue forecast. Both sources agree the category is growing, software- and cloud-heavy, and concentrated in screening, sourcing, and reporting. North America is the largest region in Mordor’s cut (41.62% of 2025 revenue).

The reference implementation is technically straightforward and operationally unsafe if copied literally. `RecruitmentCrew` runs four agents in a sequential CrewAI process: researcher, matcher, communicator, and reporter. The researcher is wired to a custom `LinkedInTool` that logs into LinkedIn with a session cookie through Selenium. The example README states that this is a Selenium demonstration, that real-world use may violate LinkedIn’s terms, and that the authors do not endorse that use. The matcher task text also tells the agent not to scrape LinkedIn. A viable MVP keeps the four-stage workflow, drops LinkedIn session automation, cites every lead, and requires a human to accept the report before any candidate is contacted. Scoring and ranking people for hiring can be a high-risk employment use under the EU AI Act Service Desk’s Annex III guidance and, in New York City, an automated employment decision tool under Local Law 144 when it substantially assists screening. The MVP is a drafting assistant with recruiter discretion, documented as such.

## 1. Market Analysis and Opportunity Assessment

### Key Insights

- Demand is real and still early among recruiters. LinkedIn measured 27% current generative-AI use or experimentation and 62% optimism in late 2023. Employ measured broader “AI to augment recruiting technology” at 63% in its 2024 report, with 89% of that group using it frequently or very frequently. The two percentages are different questions and should not be averaged.
- The work this crew automates matches the use cases recruiters already report. Employ: candidate matching 55%, intelligent sourcing 44%, intelligent candidate messaging 43%, recruitment-marketing content 40%. LinkedIn: among generative-AI users, writing and mundane-task automation lead; engagement is secondary (35%).
- Hiring has not gotten simpler. Gem’s 2025 Recruiting Benchmarks, covering January 2021–December 2024 (over 140 million applicants, 14.4 million candidates, and 1.3 million hires in Gem’s dataset), reports average time to hire rising from 33 days to 41 days and interviews per hire rising from 14 to 20. Employ reports a separate time-to-fill series falling from 48 days (2023) to 41 days (2024). Both can be true: they use different definitions and populations. The planning implication is that a shortlist draft is valuable, and a claimed reduction in days-to-fill is not an MVP success metric until this product measures it.
- Market-size publications disagree by roughly 4–5x in 2025 (Mordor USD 596 million versus QY US$2.8 billion). Mordor’s public methodology notes that blending staffing services with software, and bundled HR suites with point tools, is a known reason publishers diverge. This MRD treats Mordor as the narrower AI-recruitment software cut and QY as a wider AI-recruiting-tool cut. Neither figure is a forecast for this repository.
- Incumbents already sell sourcing, CRM, scheduling, and analytics (Gem’s own description) and natural-language search over large profile indexes (SeekOut Assist and Eightfold Recruiter Copilot, as described by SHRM). A four-agent report generator does not replace an ATS or a billion-profile index. Its opening is a transparent, requisition-scoped workflow a recruiter can run locally and audit.

### Data Points

| Topic | Figure | Publisher and date | Scope note |
| --- | --- | --- | --- |
| AI recruitment market, 2025 | USD 596.16 million | Mordor Intelligence, forecast page retrieved 2026-11-05 | Narrower AI recruitment market |
| AI recruitment market, 2026 / 2031 | USD 640.99 million / USD 920.91 million | Mordor Intelligence | 7.52% CAGR, 2026–2031 |
| AI recruiting tool market, 2025 / 2026 / 2032 | US$2,794 million / US$3,242 million / US$8,662 million | QY Research, published 2026-03-06 | Wider tool definition; 17.8% CAGR, 2026–2032 |
| Region | North America 41.62% of 2025 revenue; Asia-Pacific forecast 19.18% CAGR to 2031 | Mordor Intelligence | Geography of vendor revenue, not of this MVP |
| Deployment and application | Cloud 77.94% of 2025 size; candidate screening and assessment 31.85% | Mordor Intelligence | Screening is the largest application slice Mordor reports |
| Buyer size | Large enterprises 57.22% of 2025 spend; SMEs forecast 10.05% CAGR | Mordor Intelligence | MVP persona is an individual recruiter or small team, which is the faster-growing slice, not the largest |
| Generative AI in TA | 27% using or experimenting; ~62% optimistic | LinkedIn Future of Recruiting 2024, fieldwork Oct–Nov 2023 | Talent professionals surveyed by LinkedIn |
| AI augmenting recruiting tech | 63% (from 58%); matching 55%; sourcing 44%; messaging 43% | Employ Recruiter Nation Report 2024 | Recruiters and TA decision makers |
| Time | Gem time-to-hire 41 days in 2024 vs 33 in 2021; Employ time-to-fill 41 days in 2024 vs 48 in 2023 | Gem 2025 benchmarks; Employ 2024 | Definitions differ; see Open Questions |

Mordor also states that 70% of organizations are experimenting with AI in HR and 92% claim measurable benefits. The public summary does not name the underlying survey. Those two percentages are recorded as Mordor’s claim, not as an independent finding.

### Source Citations

See Sources S1–S12 and S14–S18. Competitive product behavior is S13 (SHRM on SeekOut and Eightfold) and S14 (Gem’s description of its own platform).

### Implications

- Position the assistant as a requisition copilot for sourcing notes, match scores, outreach drafts, and a report. Do not position it as an ATS, a talent CRM, or a labor-market data product.
- Do not publish a revenue target from either market total. The business case for this MVP is recruiter time on one req: a complete draft the operator can accept, edit, or discard.
- Geographic focus for the first version is English-language professional hiring, consistent with the example’s Ruby on Rails and React engineer requisition and with North America’s share of Mordor’s market. Multi-region compliance is a later decision, not a default claim.
- Willingness to pay is not evidenced in the sources reviewed for a local four-agent tool. Gem, SeekOut, and Eightfold sell broader platforms. Pricing for this assistant stays unresolved (Open Questions).

## 2. Technical Feasibility and Requirements Analysis

### Key Insights

- The reference crew is small and sequential. `crew.py` builds `RecruitmentCrew` with `Process.sequential`, `allow_delegation=False` on every agent, and four tasks. Only the report task sets `context` to the three prior tasks. CrewAI’s process documentation describes sequential execution as tasks in list order, with prior output available as context. That matches AAMAD’s CrewAI adapter guidance: sequential process, delegation off unless the architecture document justifies it, and `max_iter` at or below 12 for MVP tasks.
- Agent contracts are already written. `agents.yaml` defines researcher (“Job Candidate Researcher”), matcher (“Candidate Matcher and Scorer”), communicator (“Candidate Outreach Strategist”), and reporter (“Candidate Reporting Specialist”). `tasks.yaml` inputs a single `{job_requirements}` block. `main.py` demonstrates that input with a Ruby on Rails and React engineer requisition and calls `kickoff`. A training entrypoint exists (`train`) and is out of MVP scope.
- Tooling in the example does not transfer to a production assistant. The researcher receives `SerperDevTool`, `ScrapeWebsiteTool`, and `LinkedInTool`. The matcher and communicator receive Serper and scrape only. The reporter has no tools. `LinkedInTool` calls a Selenium client and returns name, position, location, and profile link. The README requires an `li_at` cookie and warns against real-world use. The matcher task says “Don't try to scrape people's linkedin, since you don't have access to it,” which conflicts with the researcher’s LinkedIn tool. The safe reading is that LinkedIn session automation is a demo hazard, not a product requirement.
- The research task’s expected output asks for “contact information” for 10 candidates. The LinkedIn tool’s formatter does not return email or phone. No source reviewed here establishes a lawful default source for personal contact details. Feasibility of “10 candidates with contact details” is therefore not established.
- The example README says the script uses GPT-4o unless changed, and that model choice changes cost. AAMAD forbids embedding secrets. Keys belong in environment variables named in `.env.example` during Build, not in this document.

### Data Points

- Four agents, four tasks, one input field (`job_requirements`), sequential process, delegation disabled (S1–S5).
- LinkedIn tool output fields observed in source: name, position, location, profile link (S6).
- CrewAI hierarchical process requires `manager_llm` or `manager_agent` (S7). The example does not use it.
- Adapter baseline: `max_iter <= 12`, `max_retry_limit >= 2`, memory off by default (S8). No measured latency or token cost for this crew was found in the example README.

### Source Citations

S1–S8.

### Implications

- Build the same role split and task order. Replace `LinkedInTool` with leads the operator pastes, plus optional web search and page fetch when the operator supplies a search API key and accepts that those calls leave the machine.
- Each lead in the report carries a source URL or the label “operator-supplied.” Scores include a short justification tied to the requisition text.
- Personal email and phone are omitted unless the operator pasted them. The example’s “contact information” line is not an MVP acceptance criterion.
- Runtime stays CrewAI YAML (`config/agents.yaml`, `config/tasks.yaml`) because `AAMAD_TARGET_RUNTIME` is unset and the adapter registry defaults to `crewai`, and because the stakeholder anchored the use case on this example. A different runtime remains an open question.

## 3. User Experience and Workflow Analysis

### Key Insights

- One primary operator: a recruiter or talent partner who already has a requisition and needs a first shortlist and a way to explain it. LinkedIn’s same report says the skills hiring professionals expect of recruiters are communication, relationship-building, and adaptability, and quotes the view that AI does not replace high-touch candidate experience. The assistant drafts; the recruiter talks to people.
- The example journey is one shot. Paste requirements, run `poetry run recruitment`, read a markdown report. There is no chat thread, no saved pipeline, and no editing loop in `main.py`.
- Employ still found 87% of respondents using spreadsheets to track recruiting data even while 84% use analytics. A markdown report the recruiter can copy into the tool they already use fits current behavior better than a new system of record.
- Full automation is a poor fit for outreach and for the hiring decision. The communicator’s expected output is “methods and templates ready for implementation,” which is a draft, not a sent message. The reporter “reports the best candidates to the recruiters,” which assumes a human recipient.
- Human oversight is required before the report is treated as a screening outcome. The EU AI Act Service Desk says an automated job-matching and ranking tool that emits scores such as “top 5” or “high fit” can still be high-risk when those scores are a primary input, even if a person may override them. NYC DCWP says screening is an employment decision under Local Law 144, and an automated employment decision tool is in scope when it substantially assists or replaces discretion.

### Data Points

- Example input: one requisition covering title, description, responsibilities, requirements, preferred qualifications, and perks (S4).
- Example outputs: 10 candidate profiles (research), a ranked list with scores and justifications (match), outreach methods and templates (communicator), a markdown report with profiles, scores, and outreach strategies (reporter) (S3).
- LinkedIn, share of generative-AI users citing easier or faster candidate engagement: 35% (S10).
- Employ, share using AI for email and recruitment-marketing content: 40%; chatbots and intelligent messaging: 43% (S12).

### Source Citations

S3, S4, S10, S12, S15, S16.

### Implications

- MVP interface is a single web form: paste the requisition, optionally paste known leads, run, then read and accept or discard the report. A chat transcript is optional and is not required to copy the example.
- The product shows agent identity on each section (who researched, who scored, who drafted outreach) so the recruiter can see the chain.
- The run ends in a review state. Accepting the report is an explicit recruiter action. The product does not email candidates in the MVP.
- Success for the operator is a usable brief on one req, not an autonomous fill.

## 4. Production and Operations Requirements

### Key Insights

- The example is a local Poetry script, not a service. It has no authentication, no tenant model, and no persistence. Those gaps are acceptable for a single-operator MVP and are not acceptable for a multi-team deployment.
- Candidate data is personal data. The report will contain names, roles, locations, and URLs whenever search or pasted leads include them. Retention, access, and notice are product requirements, not polish.
- NYC Local Law 144 applies when an employer or employment agency uses an automated employment decision tool “in the city” (NYC job location, including remote roles tied to an NYC office, or an agency located in NYC). Obligations include a bias audit no more than one year old, a public summary of that audit, and notice to NYC-resident candidates at least 10 business days before use, including how to request an alternative process. A local draft that a recruiter may ignore is not automatically an AEDT. A score that substantially drives who is screened can be. The MVP documents the boundary and does not claim a bias audit it has not performed.
- The EU AI Act Service Desk classifies recruitment and selection systems, including job matching and ranking that score or filter candidates, as high-risk under Annex III point 4(a). This MRD does not give legal advice. It records the classification risk so architecture and security do not treat ranking as an internal log.
- Observability for the MVP is the CrewAI trace of task start, task output, tool calls, and failures, stored without secrets. The adapter rule points trace logs at `project-context/2.build/logs` during Build.
- Cost is dominated by model tokens and, if enabled, search API calls. The example does not publish a per-run cost. GPT-4o is the example default and is not a requirement of this PRD’s product definition.

### Data Points

- LinkedIn cookie steps and the real-world-use warning are in the example README (S1).
- NYC enforcement of Local Law 144 began 2023-07-05; the law took effect 2023-01-01 (S15).
- Cloud deployment is 77.94% of Mordor’s 2025 AI recruitment market, expanding at a 19.05% CAGR in that forecast (S9). A single-operator MVP does not need that footprint on day one.

### Source Citations

S1, S8, S9, S15, S16.

### Implications

- MVP hosting is a single local or single-service process. Multi-region, SSO, and a bias-audit program are later work, triggered if a stakeholder uses scores to screen candidates in NYC or the EU.
- Secrets: `OPENAI_API_KEY` or the provider key the Build phase selects, and a search key only if search is enabled. `LI_AT` is not a supported variable.
- The report is written to a local artifact for the run. Retention period is an open question.

## 5. Innovation and Differentiation Analysis

### Key Insights

- The example’s useful idea is the split of labor, not the LinkedIn scraper. Research, scoring, outreach drafting, and reporting are separate outputs with separate accountability. Incumbent copilots described by SHRM collapse “paste a job description, get a search” into one step (SeekOut Assist; Eightfold Recruiter Copilot). Gem sells a broader platform (CRM, sourcing, scheduling, analytics, career sites). This assistant differentiates by showing the intermediate artifacts and by refusing to send outreach itself.
- LinkedIn’s skills-based findings support the matcher’s job: recruiters with the most skills-first searches saw 24% higher InMail acceptance than the average skills-first searcher, and LinkedIn reports that a skills focus can expand a talent pool by as much as 10x. The matcher should score against skills and responsibilities in the requisition, and should treat a degree line as preferred when the requisition marks it preferred, as the sample requisition does.
- No patent search was run. Intellectual-property freedom-to-operate is unresolved.
- Monetization is not indicated by the stakeholder request. The repository is an AAMAD application based on an MIT-licensed example (S1). A priced SaaS offer would be a different product.

### Data Points

- Skills-first InMail acceptance: +24% versus average skills-first searchers; talent-pool claim: up to 10x (S10). These are LinkedIn platform measurements, not results of this assistant.
- SeekOut’s stated aim, via SHRM: a “B+ search” from a job description in about 20 seconds, with the recruiter editing afterward (S13). That is a useful quality bar for the research stage, not a latency commitment.
- Gem vendor claims in its own benchmark PDF include sourcing “5× faster” and “half as much time” on routine tasks (S14). Treat them as vendor claims.

### Source Citations

S1, S10, S13, S14.

### Implications

- Unique value for this project: an auditable four-stage brief (leads, scores with reasons, unsent outreach, final report) on one requisition.
- Partnerships (ATS, LinkedIn official APIs, assessment vendors) are future work.
- No pricing model is recommended until a stakeholder says the assistant is for sale.

## Critical Decision Points

### Go / No-Go

- **Go**, as a single-operator drafting assistant: one requisition in; cited leads; scores with written reasons; outreach drafts; a markdown report; recruiter acceptance before the report is final; no candidate messaging.
- **No-go**, as a copy of the example’s LinkedIn cookie flow, as an unattended sourcer of personal contact details, or as an automated screening decision for NYC or EU candidates without a separate compliance design.

### Technical Architecture Choices

- Runtime: CrewAI, sequential process, four agents, delegation off, YAML configuration, tools limited to search and scrape plus the operator’s pasted text.
- Human review is a product gate even though the example does not set `human_input=True`.
- Memory off for the MVP, matching the adapter default, so runs do not silently depend on prior candidates.

### Market Positioning

- User: a recruiter or hiring operator working one professional requisition at a time.
- Alternative they use today: spreadsheets, an ATS, and a sourcing platform or manual search (Employ’s spreadsheet finding; Gem and SeekOut as the platform alternative).
- This product is the explainable draft between the requisition and those systems. It is not the system of record.

### Resource Requirements

- Define: this MRD and the PRD. Architecture (SAD) is the next persona.
- Build: one sequential crew, a minimal form to submit a requisition and read the report, and tests that the four stages return the required sections. A second engineer is not indicated by the example’s size.
- Budget: model and search API spend per run is unmeasured. Cap iterations (`max_iter <= 12`) and record token use in Build logs before promising a unit cost.

## Risk Assessment Matrix

| Risk | Level | Why it matters | Response in this phase |
| --- | --- | --- | --- |
| LinkedIn session-cookie automation copied from the example | High | README: terms risk and account loss; tool returns profile data the matcher is told not to scrape | Excluded from MVP. `LI_AT` is not a configuration this product supports |
| Scores used as a screening decision | High | EU AI Act Service Desk high-risk example; NYC AEDT if the tool substantially assists screening | Report is a draft until the recruiter accepts it. Bias audit and candidate notice are out of MVP and mandatory before any AEDT-style use |
| Invented candidates, employers, or contact details | High | Research task asks for 10 people with contact information the tool cannot lawfully or reliably supply | Every lead needs a source URL or “operator-supplied.” Missing sources fail the report |
| Personal data retained without a retention rule | High | Names and profile URLs are personal data | Retention period is an open question. MVP stores the run output locally and does not build a candidate database |
| Market-size figures used as a business case | Medium | Mordor and QY differ by several times | Both cited; neither is a revenue target |
| Time-to-fill improvement claimed from Gem or Employ benchmarks | Medium | Their populations and definitions differ, and they are not this product | MVP metric is “accepted brief produced,” not days-to-fill |
| Search API cost or failure | Medium | Serper is optional and external | Run must complete on operator-pasted leads when search is unavailable |
| Model changes the shortlist between identical runs | Medium | Generative scoring is not deterministic | Show justifications and require human acceptance; temperature policy is a Build decision recorded in that phase’s audit |
| Patent or third-party IP overlap | Low for an MVP that avoids the LinkedIn client | No patent search was performed | Recorded as open |
| Hierarchical CrewAI manager added early | Low | Extra cost and less reproducible than the example | Stay sequential unless the SAD changes it |

## Actionable Recommendations

### Immediate (this Define pass)

- Write the PRD from this MRD and from the example’s agent and task files.
- Lock the MVP boundary: four stages, human acceptance, no LinkedIn cookie tool, no outbound messages, no contact-detail requirement.
- Hand the PRD to the system architect for the SAD. Do not start application code in this persona.

### Short term (Build, after the SAD)

- Implement the crew in YAML with the adapter’s iteration, retry, and logging caps.
- Accept a pasted requisition and an optional pasted lead list. Enable web search only behind an operator-provided key.
- Validate the report headings in QA: leads, scores and justifications, outreach drafts, sources.

### Longer term (only with a new decision)

- Official talent-data APIs, ATS export, sent outreach, multi-user accounts, and a bias-audit package if the operator intends scores to drive screening in NYC or the EU.
- Any price or packaging decision, which this research does not support.

## Sources

1. crewAIInc/crewAI-examples, `crews/recruitment/README.md` (MIT; LinkedIn-cookie disclaimer; GPT-4o default; author João Moura). Retrieved 2026-11-05. https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/README.md
2. Same repository, `crews/recruitment/src/recruitment/config/agents.yaml`. Retrieved 2026-11-05. https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/config/agents.yaml
3. Same repository, `crews/recruitment/src/recruitment/config/tasks.yaml`. Retrieved 2026-11-05. https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/config/tasks.yaml
4. Same repository, `crews/recruitment/src/recruitment/main.py` (sample Ruby on Rails and React requisition; `kickoff` and `train`). Retrieved 2026-11-05. https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/main.py
5. Same repository, `crews/recruitment/src/recruitment/crew.py` (tools, `allow_delegation=False`, `Process.sequential`, report-task context). Retrieved 2026-11-05. https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/crew.py
6. Same repository, `crews/recruitment/src/recruitment/tools/linkedin.py` (`Retrieve LinkedIn profiles`; fields name, position, location, profile link). Retrieved 2026-11-05. https://github.com/crewAIInc/crewAI-examples/blob/main/crews/recruitment/src/recruitment/tools/linkedin.py
7. CrewAI documentation, “Processes” (sequential and hierarchical). Retrieved 2026-11-05. https://docs.crewai.com/concepts/processes
8. This project, `.cursor/rules/adapter-crewai.mdc` and `.cursor/rules/adapter-registry.mdc` (sequential MVP defaults; `AAMAD_TARGET_RUNTIME` default `crewai`). Read 2026-11-05.
9. Mordor Intelligence, “AI Recruitment Market Size & Share Analysis - Growth Trends and Forecast (2026–2031).” Page retrieved 2026-11-05. https://www.mordorintelligence.com/industry-reports/ai-recruitment-market
10. LinkedIn Talent Solutions, “The Future of Recruiting 2024” (PDF). Fieldwork October–November 2023; 1,453 recruiting professionals and 498 hiring managers; 23 countries. https://business.linkedin.com/content/dam/me/business/en-us/talent-solutions/resources/pdfs/future-of-recruiting-2024.pdf
11. LinkedIn Talent Blog summary of that report, “The Future of Recruitment: Look for an AI Supercharge and a Focus on Quality of Hire.” Retrieved 2026-11-05. https://www.linkedin.com/business/talent/blog/talent-acquisition/future-of-recruitment-ai-supercharge-focus-on-quality-of-hire
12. Employ, “2024 Recruiter Nation Report: Empowering People-First Recruiting” (PDF, hosted by Jobvite). Retrieved 2026-11-05. https://pages.jobvite.com/rs/659-JST-226/images/2024-Employ-Recruiter-Nation-Report-Empowering-People-First-Recruiting.pdf
13. SHRM, “How LLMs Are Supercharging AI-Powered Talent Intelligence” (SeekOut Assist and Eightfold Recruiter Copilot). Retrieved 2026-11-05. https://www.shrm.org/topics-tools/news/technology/how-llms-supercharging-ai-powered-talent-intelligence
14. Gem, “2025 Recruiting Benchmarks” (PDF; dataset January 2021–December 2024 and Gem product claims). Retrieved 2026-11-05. https://lp.gem.com/rs/972-IVV-330/images/2025%20Recruiting%20Benchmarks%20-%20Gem.pdf
15. NYC Department of Consumer and Worker Protection, “Automated Employment Decision Tools: Frequently Asked Questions” (Local Law 144). Retrieved 2026-11-05. https://www.nyc.gov/site/dca/businesses/faq-automated-employment-decision-tools.page
16. European Commission AI Act Service Desk, “Employment” (Annex III recruitment and ranking example). Retrieved 2026-11-05. https://ai-act-service-desk.ec.europa.eu/en/employment-0
17. NYC Council file Int. 1894-2020, Local Law 144 bill text and summary (bias audit, notice, penalties). Retrieved 2026-11-05. https://legistar.council.nyc.gov/LegislationDetail.aspx?GUID=B051915D-A9AC-451E-81F8-6596032FA3F9&ID=4344524
18. QY Research, “AI Recruiting Tool - Global Market Share and Ranking, Overall Sales and Demand Forecast 2026-2032,” published 2026-03-06. Retrieved 2026-11-05. https://www.qyresearch.com/reports/6024908/ai-recruiting-tool
19. crewAIInc/crewAI-examples, `crews/README.md` (recruitment listed as “Automates candidate sourcing and evaluation”). Retrieved 2026-11-05. https://github.com/crewAIInc/crewAI-examples/blob/main/crews/README.md
20. This project, `.cursor/templates/mrd-template.md`, `.cursor/agents/product-mgr.md`, and `aamad.config.example.yml` (schema only; `aamad.config.yml` is not present and was not applied). Read 2026-11-05.

## Assumptions

- The stakeholder request to base the use case on the CrewAI recruitment example means the four roles, four tasks, sequential order, and `{job_requirements}` input are in scope. It does not mean the LinkedIn cookie tool is in scope. The example README is the authority for that exclusion.
- `AAMAD_TARGET_RUNTIME` is unset and `aamad.config.yml` is absent. The adapter registry’s default is `crewai`. The example file `aamad.config.example.yml` also sets `runtime.target: crewai`, but an example file is not project configuration and was not loaded.
- “Recruitment assistant” means one recruiter (or one hiring operator) working one requisition at a time. No company, team size, or industry was specified. The sample requisition is software engineering; the workflow is not limited to that job family.
- Market-facing research was requested, so this MRD was written. The MVP itself is an operator tool, not a launched commercial product. Go-to-market pricing is deferred in the PRD.
- Mordor’s 70% and 92% HR-AI statements are unverified beyond Mordor’s page. They are not used as product targets.
- Gem’s speed and time-saved multiples, and SeekOut’s “20 seconds,” are vendor or interview statements. They are not acceptance criteria.
- A web form is enough UI because the example is a single input and a single report. A chat UI is allowed later if the architect prefers the AAMAD default chat pattern; it is not required to satisfy the example.
- No primary SHRM benchmarking microdata was retrieved. Secondary posts quoting SHRM cost-per-hire of about USD 4,700 and time-to-fill of 44 days were not used, because the primary table was not opened.
- Patent databases were not searched.
- This document does not provide a legal opinion on Local Law 144 or the EU AI Act. It records the published classification tests so later phases can design for them.

## Open Questions

- Should a run with no search API and no pasted leads fail, or may the researcher return an explicit empty shortlist? Recommended default: fail the research stage with a clear reason, and still allow match, outreach, and report when the operator pasted leads.
- What retention period applies to reports that contain names and profile URLs?
- Will any user run this against candidates for NYC jobs or EU hiring decisions? If yes, SAD and security need a bias-audit and notice design before those runs are allowed.
- Is the assistant only for the recruiter who operates it, or will hiring managers receive the report? The example says “report the best candidates to the recruiters.”
- Which model and provider are approved? The example uses GPT-4o. This project has not selected a key or a spend cap.
- Is web search required in the MVP, or is pasted-lead scoring enough for the first demo?
- Should degree requirements be down-weighted by default, given LinkedIn’s skills-based findings, when the requisition lists a degree as required rather than preferred?
- Is there a budget, a deadline, or a requirement to sell this assistant? None was stated.
- Does “contact information” in the example task remain a stakeholder requirement if the only lawful source is data the operator already has?

## Audit

- **Timestamp**: 2026-11-05T19:20:00-08:00
- **Persona id**: `product-mgr`
- **Action**: `create-mrd`
- **AAMAD_TARGET_RUNTIME**: `crewai`
- **Runtime warning**: the environment variable was unset and `aamad.config.yml` was not present. Resolved to `crewai` by `.cursor/rules/adapter-registry.mdc`. The stakeholder’s use case is the CrewAI recruitment example, which matches that default. `aamad.config.example.yml` was read as schema only.
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed and were not set by the operator.
- **Tools**: local reads of the product-manager persona, MRD template, adapter rules, and `aamad` validator; web retrieval of the CrewAI example source files, CrewAI process docs, and the market and compliance pages listed under Sources. Pages were retrieved on 2026-11-05.
- **Prompt Trace**: Operator request, verbatim in substance: create an MRD and a PRD for a recruitment assistant whose use case is the CrewAI recruitment example; run `*create-mrd` then `*create-prd`; complete Sources, Assumptions, Open Questions, and Audit. The IDE system prompt is omitted. No separate elicitation questionnaire was run; the example source and this research are the inputs. A system description file was not written because the operator ordered MRD then PRD directly and the example specifies the workflow.
- **Output path**: `project-context/1.define/mrd.md`
