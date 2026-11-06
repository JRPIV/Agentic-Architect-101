# QA: Recruitment Assistant

## Actions

| Action | Result |
| --- | --- |
| `test-unit` | 16 pytest checks passed. None call a model |
| `test-integration` | The same pytest run covers the page and API routes with a stubbed crew. A separate production-executor check fails an empty-lead run before kickoff |
| `qa` / `verify-flow` | Browser smoke of draft, accept, discard, satisfaction, and the hiring-manager view, using synthetic candidates |
| `log-defects` | No demo-blocking defect |
| `future-work` | Live model, search-on sourcing, and a down-model call remain untested |

The PRD acceptance criteria are bullets under F1–F6. They are not labeled `AC-*`. The map below uses `F1.1` and so on in the order those bullets appear.

## Simulated and live

| Check | Kind | Model called |
| --- | --- | --- |
| `pytest` in `backend/tests` | Simulated. The API tests replace the crew executor. Guardrail and crew-wiring tests do not call `kickoff` | No |
| Browser smoke on `127.0.0.1:8000` | Simulated. That process used a local executor that wrote synthetic candidates from the pasted leads. `OPENAI_API_KEY` was unset. `SERPER_API_KEY` was empty. Runs were stored under `/tmp/recruitment-qa-smoke`, not `backend/runs` | No |
| Empty pasted leads on the production executor | Production code path, not a live model run. `kickoff_run` returned at research before constructing the crew. No `prompt-*.json` file was written | No |
| Live crew with a model provider | Not run | No |

Token usage for this QA pass is zero. No provider reported usage because no model request was sent.

## Unit

Command, from `recruitment-assistant`:

```bash
.venv/bin/python -m pytest
```

Result: `16 passed` in 1.07s on Python 3.13.18. CrewAI 1.15.36 emitted deprecation warnings while building the crew object in `test_crew_config.py`. That test does not kick off the crew.

| Test | Criterion | Result |
| --- | --- | --- |
| `test_f1_requires_title_and_requirements` | F1.2 missing title or requirements names the field | Pass |
| `test_one_active_run_then_f1_through_f5` | F1.3 submitted text is stored; F5.1 and F5.2 score 1–5 after draft; one active run | Pass |
| `test_empty_research_without_leads_fails` | F2.3 zero candidates does not invent people | Pass |
| `test_research_rejects_more_than_ten_and_web_without_url` | F2.2 source URL required for web; F2.3 at most 10 | Pass |
| `test_operator_supplied_candidates_must_appear_in_pasted_leads` | F2.1 operator-supplied; F2.4 email must be in the paste | Pass |
| `test_crew_is_sequential_and_tools_follow_the_search_key` | F2.5 LinkedIn tool is not callable; task ids `research_candidates`, `evaluate_candidates`, `recommend_candidates`; search off means no Researcher tools | Pass |
| `test_evaluator_rejects_invented_id_and_scores_missing_evidence_as_one` | F3.1 no invented person; F3.3 missing evidence scores 1 | Pass |
| `test_ranking_orders_by_score_and_keeps_researcher_ties` | F4.1 score descending, ties keep Researcher order | Pass |
| `test_recommendation_rejects_outreach_field_and_unknown_id` | F4.3 no outreach field; ranked ids must be sourced | Pass |
| `test_discard_does_not_accept_and_failed_run_cannot_be_accepted` | F4.4 discard is not accepted; accept from `failed` is `invalid_state`; F5 rejects a score before draft | Pass |
| `test_log_redacts_secret_values` | Logs do not keep an API key value | Pass |
| `test_posting_text_does_not_create_a_run_and_blocks_private_urls` | F6.1 pasted text fills fields; F6.3 no writeback and no run; private URL does not start the crew | Pass |
| `test_fetch_stops_when_stream_exceeds_size_limit`, `test_fetch_reads_a_stream_that_fits` | F6 URL body cap | Pass |
| `test_startup_marks_stale_run_failed` | A restarted process does not leave a run accepted | Pass |

`LI_AT` was unset in the crew-wiring test. `backend/requirements.txt` has no Selenium, LinkedIn, SMTP, or messaging client.

## Integration

These checks cross the page, the API, and the runtime boundary. They are still simulated except for the production empty-lead return, which does not call a model.

| Test | Criterion | Result |
| --- | --- | --- |
| `test_pages_share_the_api_origin` | Recruiter and hiring-manager HTML, CSS, and JS come from the API origin. The hiring-manager page has no Run, Accept, or Discard control. A stubbed empty-lead run ends `failed` at research and the recommendation stays 404 | Pass |
| `test_one_active_run_then_f1_through_f5` | Scripted Ruby on Rails and React requisition, stubbed crew, `source_elapsed_ms` present, accept stores label and time, recommendation markdown includes the contact disclaimer | Pass |
| `test_discard_does_not_accept_and_failed_run_cannot_be_accepted` | Recommendation GET is 404 until `accepted`. A second start while a run is active is 409 in the companion test | Pass |
| Production executor, empty pasted leads, `SERPER_API_KEY` empty, no `OPENAI_API_KEY` | F2.3. Status `failed`, stage `research`, message "No pasted leads and search is off. The Researcher does not invent people." `accepted_at` null. Recommendation 404. No prompt file | Pass |

The first poll of that production check returned while the background thread was still starting. A wait of under a second showed `failed`. That was the test harness, not a stuck run.

## Smoke

Browser: `http://127.0.0.1:8000/`, simulated executor, synthetic people only.

Requisition: title "Ruby on Rails and React engineer", requirements "Ruby on Rails", responsibilities "Ship features", preferred "React", perks "Remote". The fields were filled from pasted posting text. Status stayed "no run yet" and the preview said the crew had not started.

| Step | What the page showed | Result |
| --- | --- | --- |
| Empty form | Run, Accept, Discard, and Save score disabled | Pass, F1.2 |
| Pasted posting text, Fill fields | Title and requirements filled. No run created | Pass, F6.1 and F6.3 |
| Run with no pasted leads | "Status: failed. Stage: research. No pasted leads and search is off. The Researcher does not invent people." No candidate. Accept and Save score stayed disabled. Run id `9028f504-af2c-40be-93ad-4e25577c5320` | Pass, F2.3 |
| Pasted leads for Ada Lovelace (`ada@example.test`) and Grace Hopper (`grace@example.test`), then Run | Draft. Source time 0.0 s (42 ms). Both rows `operator-supplied`. Ada score 5, met Ruby on Rails and React. Grace score 2, met React, missing Ruby on Rails. Rank 1 Ada, rank 2 Grace. Run id `aebbe413-6f3d-4d28-89f3-d8558495cbb1` | Pass, F2.1, F3.2, F4.1, time-to-source |
| Hiring manager before accept | "Status: draft. This run is not accepted yet." No ranking and no Accept control | Pass, F4.5 |
| Satisfaction 4 and comment "Synthetic shortlist was usable." | "Saved satisfaction score: 4 of 5." The score was still there after accept and after reload | Pass, F5.1 and F5.2 |
| Accept with label "Jamie Recruiter" | "Status: accepted. Accepted at 2026-11-06T05:52:14.413183+00:00 by Jamie Recruiter." Accept and Discard disabled | Pass, F4.4 |
| Hiring manager after accept | Ranking rendered. Ada 5 of 5, then Grace 2 of 5. Disclaimer present. No Run, Accept, or Discard | Pass, F4.2 and F4.5 |
| Second run, pasted lead "Lin Example", then Discard and Discard draft | Recruiter status discarded at 2026-11-06T05:53:13.383946+00:00. Lin Example stayed readable. Hiring manager: "This run was discarded. It is not a recommendation." Run id `10fe54dd-92d0-4290-979e-9ff89fa592e5` | Pass, F4.4 |

The ranking text on both pages says contact decisions happen outside this product. The pages have no send control and no analytics, inbox, or pipeline view. Across this pass, the product sent zero messages.

The smoke server log has the posting preview, the run creates, the satisfaction `200`, and the accept `200`. It has no prompt file.

## Defects

No demo-blocking defect. No application code was changed in this pass.

## Remaining gaps

- A live model run was not executed. Pasted leads on the production executor will call the model when a key is set. This pass does not claim that path succeeds.
- Search-on sourcing was not run. The guardrail rejects a web row without `source_url`. An accepted run that contains a web row was not produced.
- A down model was not called. The code marks an exception `failed` and does not set `accepted`. The failed-state test covers the API rule with a stored failure, not a live provider error.
- F6 URL preview was not clicked in the browser. API tests reject a private URL and a non-public example URL. Pasted posting text is the path this smoke used.
- The hiring-manager page still reads the full run document to tell draft, discarded, and failed apart. It does not render the ranking unless the recommendation GET returns 200.
- The optional CLI is not in this slice. The two pages are the interface the PRD requires for accept, discard, and satisfaction.
- Preferred-versus-required weighting is prompt text. The code does not parse which phrase is preferred.
- Numeric targets for time to source, match accuracy, and satisfaction average are still open in the PRD.
- `@security.eng` has not written `security.md`. The SAD recommends that assessment before Deliver.

## Future work

- One live crew run with pasted synthetic leads and a model key, then the same accept and hiring-manager checks on that output.
- One search-on run, confirming every web row in the accepted ranking has `source_url`.
- One run with the model unavailable, confirming the page shows `failed` and the recommendation stays hidden.
- Frontend coverage for the poll, the discard confirmation, and the hiring-manager states. This pass used the browser, not a frontend test file.
- Status-only response so the hiring-manager page can distinguish draft, discarded, and failed without receiving the draft ranking.

## Sources

- `project-context/1.define/prd.md` (F1–F6, success metrics, Quality Assurance Checklist)
- `project-context/1.define/sad.md` Section 9
- `project-context/2.build/backend.md`
- `project-context/2.build/frontend.md`
- `project-context/2.build/integration.md`
- `.cursor/agents/qa-eng.md`
- `.cursor/rules/adapter-crewai.mdc`
- No `aamad.config.yml`. No `setup.md`. No `system-description.md`. No user stories.

## Assumptions

- `AAMAD_TARGET_RUNTIME` was unset in this agent shell. It resolves to `crewai` from the SAD, the PRD, and the adapter registry default.
- The operator asked for Tier-0 QA plus the Step 7 documentation updates in `README.md`, `backend.md`, and `frontend.md`. Those doc edits are part of this pass. No commit was requested.
- Synthetic names (Ada Lovelace, Grace Hopper, Lin Example) and `@example.test` addresses are fixture data. They are not sourced people.
- The 42 ms source time in the browser is the simulated executor's fixture value. It shows that the page renders `source_elapsed_ms`. It is not a measurement of a model call.
- `aamad.config.yml` is absent, so no testing preference in that file was applied.

## Open Questions

- Carried from the PRD and SAD: time-to-source minute target, match-accuracy percentage, satisfaction average, retention, NYC or EU employment use, and whether a degree may outweigh skills.
- Is a pasted-lead demo enough for the first live crew run, or is Serper required?
- Should `@security.eng` run before Deliver? The example config asks for a security assessment. The PRD module map does not assign that persona. This file does not start that assessment.

## Audit

- **Timestamp**: 2026-11-05T21:54:10-08:00
- **Persona id**: `qa-eng`
- **Action**: `test-unit`, `test-integration`, `qa`, `verify-flow`, `log-defects`, `future-work`
- AAMAD_TARGET_RUNTIME: crewai
- **Runtime warning**: `AAMAD_TARGET_RUNTIME` was unset in this agent shell and `aamad.config.yml` was not present. Resolved to `crewai` from the SAD, the PRD, and `.cursor/rules/adapter-registry.mdc`.
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed and were not set. The application crew was not kicked off. No live model run.
- **LLM controls recorded for the application**: model name from `OPENAI_MODEL`, default `gpt-4o`; temperature `0.2`; max_tokens `4096`. Those controls were not used in this pass.
- **Tests**: `16 passed` via `.venv/bin/python -m pytest`. Browser smoke used a simulated executor and synthetic candidates.
- **Code changes**: none. Documentation updates: this file, `README.md`, the stale "pages are not served" statements in `backend.md` and `frontend.md`, and the integration known-gap line that still said those statements were current.
- **Prompt Trace**: The operator asked to complete Tier-0 QA, review the PRD, SAD, backend.md, frontend.md, and integration.md, run the tests, smoke-test draft, accept, discard, satisfaction, and the hiring-manager view with synthetic data, distinguish simulated tests from any live model run, fix only demo-blocking issues, write this file, update the README and the stale page-serving lines, and not commit. System-prompt text is omitted.
- **Output path**: `project-context/2.build/qa.md`
- **Handoff**: `@security.eng` is the recommended next persona before Deliver. `@devops.eng` waits on that assessment or an explicit decision to proceed without it.
