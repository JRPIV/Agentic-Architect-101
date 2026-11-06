# Execution results: Recruitment Assistant

This file records the Module 07 checks run on 2026-11-05. Simulated checks and the live crew attempt are separate.

Local delivery and simulated validation complete. Successful live CrewAI execution remains unverified because API credits were unavailable.

The simulated checks do not prove live model behavior. The live crew did not produce a draft. The operator will not purchase credits, and this attempt will not be retried.

## Simulated checks

These checks do not call a model.

| Check | When | Result |
| --- | --- | --- |
| `.venv/bin/python -m pytest` | 2026-11-05, after the logging edits, before the server start | `17 passed` in 0.86s on Python 3.13.18. CrewAI deprecation warnings while building the crew object. No kickoff |
| Same command after the final logging edit | 2026-11-05, after the server had stopped | `17 passed` in 1.06s. No kickoff |

The API tests replace the crew executor. `test_one_active_run_then_f1_through_f5` stores a synthetic draft for Ada Lovelace, accepts it as "Jamie Recruiter", and reads the recommendation, including the contact disclaimer. `test_pages_share_the_api_origin` checks that the hiring-manager HTML has no Run, Accept, or Discard control. `test_request_log_records_metadata_without_candidate_text` checks that `app.log` records the POST path and status and does not record the pasted lead or the test key.

That is the draft, accept, and hiring-manager coverage from this pass. It is simulated. The earlier browser pass in `project-context/2.build/qa.md` is also simulated. This pass did not repeat that browser script.

## Environment check

`.env` was not modified and its values were not printed. A local classifier reported only absent, empty, placeholder, or configured.

| Name | In `.env` | In the shell before startup |
| --- | --- | --- |
| `OPENAI_API_KEY` | Configured. Not the example placeholder | Absent |
| `OPENAI_MODEL` | Configured | Not checked in the shell |
| `AAMAD_TARGET_RUNTIME` | Configured | Not checked in the shell |
| `APP_NAME` | Configured | Not checked in the shell |
| `APP_ENV` | Configured | Not checked in the shell |
| `CREWAI_TELEMETRY_OPT_OUT` | Configured | Set to `true` for the server process |
| `CREWAI_TRACING_ENABLED` | Absent | Set to `false` for the server process |
| `SERPER_API_KEY` | Absent | Set empty for the server process |

The server was started without putting the model key on the command line. CrewAI loads `.env` when the crew module is imported. The provider response below shows that a key was presented. The key text was not copied into this file.

## Startup procedure

Command, from `recruitment-assistant`, at 2026-11-06T06:56:31Z:

```bash
SERPER_API_KEY= CREWAI_TRACING_ENABLED=false CREWAI_TELEMETRY_OPT_OUT=true .venv/bin/python -m backend
```

The empty `SERPER_API_KEY` was process environment only. `.env` was not rewritten.

| Check | Timestamp | Result |
| --- | --- | --- |
| Process log | 2026-11-05 22:56:32 local | `startup host=127.0.0.1 port=8000 telemetry_opt_out=true crewai_tracing=false` and `Uvicorn running on http://127.0.0.1:8000` |
| `GET /health` | 2026-11-06T06:57:13.816067+00:00 | `200`, 15 bytes |
| `GET /` | 2026-11-06T06:57:13.838886+00:00 | `200`, 5814 bytes |
| `GET /hiring-manager` | 2026-11-06T06:57:13.841775+00:00 | `200`, 1435 bytes |
| `GET /css/app.css` | 2026-11-06T06:57:13.842941+00:00 | `200`, 2741 bytes |
| `GET /js/api.js` | 2026-11-06T06:57:13.843990+00:00 | `200`, 2526 bytes |
| `GET /api/runs/does-not-exist` | 2026-11-06T06:57:13.844905+00:00 | `404` |
| `lsof -nP -iTCP:8000 -sTCP:LISTEN` | During the run | `127.0.0.1:8000` |
| `kill -TERM` | 2026-11-05 22:59:59 local | `shutdown` in `app.log`. Process exit status 143. Port 8000 free |

`GET /health` does not call the model.

## Live execution

One crew kickoff. Web search was off. The run failed before evaluation, recommendation, accept, or a hiring-manager ranking.

### Input

`POST /api/runs` at 2026-11-06T06:57:13.845785+00:00.

```json
{
  "requisition": {
    "title": "Platform engineer",
    "description": "Synthetic requisition for one local crew check.",
    "responsibilities": "Keep a small service running.",
    "requirements": "Python",
    "preferred_qualifications": "FastAPI",
    "perks_and_benefits": "Remote"
  },
  "pasted_leads": "Sam Rivera, platform engineer, Python and FastAPI, sam.rivera@example.test"
}
```

Sam Rivera and `sam.rivera@example.test` are synthetic. They are not a sourced person.

Response: `202` `{"run_id": "9481a8b0-1e3c-4c9f-8e67-cedbe696e768", "status": "researching"}`.

Prompt trace `project-context/2.build/logs/prompt-9481a8b0-1e3c-4c9f-8e67-cedbe696e768.json` recorded model `gpt-4o`, temperature `0.2`, `max_tokens` `4096`, and `search_enabled` `false`. That file includes the synthetic pasted lead because it is the prompt record. `app.log` did not contain `sam.rivera@example.test`.

### Timeline

| Timestamp | Observation |
| --- | --- |
| 2026-11-06T06:57:13.847018+00:00 | First poll: `researching` |
| 2026-11-05 22:57:14 local | `crew event=task_start task=research_candidates search_enabled=False tools=` |
| 2026-11-06T06:57:16.854920+00:00 through 2026-11-06T06:57:40.953216+00:00 | Nine more polls, all `researching` |
| 2026-11-05 22:57:42 local | `crew event=task_failed stage=research error_class=RuntimeError` |
| 2026-11-06T06:57:43.961354+00:00 | Poll: `failed` |
| 2026-11-06T06:58:15Z request | `GET /api/runs/9481a8b0-1e3c-4c9f-8e67-cedbe696e768/recommendation` returned `404` `invalid_state` |
| 2026-11-05 22:59:00 local | Browser opened `http://127.0.0.1:8000/hiring-manager?run_id=9481a8b0-1e3c-4c9f-8e67-cedbe696e768` |

`source_elapsed_ms` on the failed run is `27690`. That is the time until research failed. It is not a completed source time. `candidates` and `ranking` are null. `accepted_at`, `recruiter_label`, and `discarded_at` are null.

### Output

Stored error, stage `research`:

```text
RuntimeError: Task execution failed: Error code: 429 - {'error': {'message': 'You have no credits remaining. Add credits to continue using the API at https://platform.openai.com/settings/organization/billing/.', 'type': 'insufficient_quota', 'param': None, 'code': 'credit_balance_exhausted'}}
```

The hiring-manager page showed `Status: failed. Stage: research.` and the same provider text. The visible controls were Open and Check again. There was no ranking and no Accept, Discard, or Run control.

No accept request was sent. Evaluator and Recommender did not start.

### Secret scan for this run

The model-key value from `.env` was compared with the execution note, `app.log`, `server-deliver.out`, `trace.jsonl`, and the prompt file. It did not appear in those files. This document does not contain it.

## Issues

- Live result: the configured model key was presented and OpenAI returned HTTP 429 `insufficient_quota` / `credit_balance_exhausted`. Research failed. The draft, accept, and accepted hiring-manager ranking were not exercised on live output. Successful live CrewAI execution remains unverified because API credits were unavailable. The call will not be retried.
- Search-on sourcing was not run.
- `security.md` is still absent.
- CI and `project-context/3.deliver/user-guide.md` were not part of this closeout.

## Sources

- `project-context/2.build/qa.md` (earlier simulated browser pass; not repeated here)
- `project-context/3.deliver/deploy.md`
- `backend/runs/9481a8b0-1e3c-4c9f-8e67-cedbe696e768/run.json` (status and error only; the file is gitignored)
- `project-context/2.build/logs/app.log`, `trace.jsonl`, and `prompt-9481a8b0-1e3c-4c9f-8e67-cedbe696e768.json` (gitignored)
- Pytest output from this pass: `17 passed`

## Assumptions

- `AAMAD_TARGET_RUNTIME` in `.env` is configured. The application resolves `crewai`. The value was not printed.
- The 429 body is the provider's text as stored on the run. It names a billing URL. It does not name the key.
- The hiring-manager browser check is a live view of the failed run. It is not an accept check.

## Open Questions

- Successful live CrewAI execution remains unverified because API credits were unavailable. This exercise does not leave a rerun open.

## Audit

- **Timestamp**: 2026-11-05T23:00:49-08:00
- **Persona id**: `devops-eng`
- **Action**: live execution record for Module 07
- AAMAD_TARGET_RUNTIME: crewai
- **Model**: The application prompt trace recorded `gpt-4o`, temperature `0.2`, `max_tokens` `4096`. The provider rejected the research call with 429 before a ranking existed. The Cursor session model was Grok 4.7. Its temperature and max_tokens were not exposed.
- **Live result**: failed. Not accepted. Do not treat this file as a passing crew run. Local delivery and simulated validation complete. Successful live CrewAI execution remains unverified because API credits were unavailable.
- **Prompt Trace**: The operator asked for the remaining Module 07 work: logging, execution, lessons, documentation, and verification, on `feature/deliver`, without a commit. System-prompt text is omitted.
- **Output path**: `project-context/3.deliver/execution-results.md`
