# Deploy: Recruitment Assistant

Module 07 runbook for the local Tier-0 process. No cloud resource was created. Local delivery and simulated validation complete. Successful live CrewAI execution remains unverified because API credits were unavailable. The simulated tests do not prove live model behavior. The failed attempt stays in `project-context/3.deliver/execution-results.md`. `security.md` is still absent. CI and the optional user guide were not added.

## Release scope

Release name: local Tier-0 MVP. There is no version tag. The Git root is this `recruitment-assistant` directory. `feature/deliver` and `main` are both at `cfa691f` (`docs: Complete Tier-0 QA and Build documentation`). That commit is the current committed baseline. Deliver edits after it are uncommitted. The parent `Agentic Architect 101` folder is a different repository and is not this application's history.

In this release:

- Python 3.13.18, CrewAI 1.15.36, FastAPI 0.162.0, and Uvicorn 0.54.0.
- One process serves the recruiter page, the hiring-manager page, and the API.
- The crew remains Researcher, Evaluator, and Recommender, sequential, with the existing YAML in `backend/config/`.
- Run records stay files under `backend/runs/`.
- `GET /health` reports process liveness and does not call a model.

QA in `project-context/2.build/qa.md` passed 16 pytest checks and a browser pass of draft, accept, discard, satisfaction, and the hiring-manager view. That browser pass used synthetic candidates and did not call a model. This pass ran pytest again after the logging edits: 17 passed in 1.06s on Python 3.13.18. Those tests stub the crew.

A live crew run was attempted with one synthetic pasted lead and search off. OpenAI returned HTTP 429 `credit_balance_exhausted` during research. The run is `failed` and was not accepted. That attempt is not a successful live execution. Simulated pytest and the QA browser pass do not prove live model behavior. Search-on sourcing was not run. See `execution-results.md`.

`project-context/2.build/security.md` is absent. The operator accepted that gap for this local Tier-0 exercise. See Assumptions.

Still outside this mini-project: full ATS integration, candidate messaging, analytics dashboards, LinkedIn session-cookie login, and a commercial or cloud launch.

## Hosting approach

The host is the operator's machine. One process listens on `127.0.0.1:8000`.

| Item | Value |
| --- | --- |
| Runtime | `crewai` |
| Interpreter | Python 3.13.18 |
| Application object | `backend.app:app` |
| Start module | `python -m backend` (`backend/__main__.py`) |
| Bind | `127.0.0.1:8000` |
| Health | `GET /health` → `{"status":"ok"}` |
| Pages | `/` and `/hiring-manager` |
| Dependencies | `backend/requirements.txt` (direct pins) and `backend/requirements.lock.txt` (151 pins) |

`Dockerfile` packages that same module. It installs `backend/requirements.lock.txt`, copies `backend/`, `frontend/`, and `pytest.ini`, and runs `python -m backend` as uid 10001. `.dockerignore` keeps `.env`, `.venv`, `backend/runs/`, and `project-context/2.build/logs/` out of the build context. The image listens on the container loopback because `backend/__main__.py` sets that bind. A published container port does not reach that address. `docker` is not installed on this machine, so the image was not built and not started. The procedure below is the one that ran.

## Environment variables

Names only. Secret values stay in the operator's `.env`, which is gitignored. This runbook does not record them.

| Name | Required | In `.env.example` | What the process does with it |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Required for a live crew run. The process and `GET /health` start without it | Yes. Placeholder only | Model credential. CrewAI reads it after `crewai.llm` loads `.env` from the working directory on the first crew import |
| `OPENAI_MODEL` | No | Yes. Example `gpt-4o` | Model id. Unset uses `gpt-4o` |
| `AAMAD_TARGET_RUNTIME` | No | Yes. Example `crewai` | Must stay `crewai` for this SAD. The application code does not branch on it. Unset resolves to `crewai` |
| `APP_NAME` | No | Yes. Example `Recruitment Assistant` | Current process does not read it. The FastAPI title is the same string in `backend/app.py` |
| `APP_ENV` | No | Yes. Example `development` | Current process does not read it |
| `CREWAI_TELEMETRY_OPT_OUT` | No | Yes. Example `true` | `backend/__main__.py` and `backend/crew.py` default it to `true` when it is unset. This does not disable CrewAI execution tracing |
| `CREWAI_TRACING_ENABLED` | No | Yes. Example `false` | CrewAI 1.15.36 execution tracing. After `.env` loads, `backend/crew.py` sets this to `false` when it is unset. `true` opts in. The crew object does not pass `tracing=True` |
| `SERPER_API_KEY` | No | Yes. Empty | Empty keeps search off. Pasted leads are the only source. A non-empty value binds Serper and page scrape on the Researcher only |
| `BACKEND_RUNS_DIR` | No | No. Code override | Unset uses `backend/runs` |
| `BACKEND_LOG_DIR` | No | No. Code override | Unset uses `project-context/2.build/logs` |

`LI_AT` is not a variable. Do not add it.

## Installation

From `recruitment-assistant`. On this machine `python3` is 3.14.10, and `python3.13` is not on `PATH`. CrewAI 1.15.36 requires Python `>=3.10,<3.14`. uv 0.13.7 resolves the interpreter:

```bash
uv python find 3.13 --system
uv venv --python 3.13 .venv
uv pip install -r backend/requirements.txt --python .venv/bin/python
```

The lock file is the pin to reinstall when the tree must match a known set:

```bash
uv pip install -r backend/requirements.lock.txt --python .venv/bin/python
```

When `.env` is absent, copy the example and set `OPENAI_API_KEY` locally. Leave `SERPER_API_KEY` empty for pasted leads only.

```bash
cp .env.example .env
```

This machine already had `.venv` and `.env`. The copy was not run. `.env` was not read. `uv venv --python 3.13` was run in a temporary directory, reported CPython 3.13.18, and that directory was removed. The project `.venv` was left in place. `uv pip install --offline` against that `.venv` checked 4 packages from `backend/requirements.txt` and 151 packages from `backend/requirements.lock.txt`. A download into an empty environment was not repeated.

`.venv/bin/python -m pip` fails here with `No module named pip`. The validated installer is `uv pip`.

## Startup

Working directory: `recruitment-assistant`. The `backend` package is the source tree, so the process is started from that directory.

```bash
.venv/bin/python -m backend
```

`backend/__main__.py` calls Uvicorn on `backend.app:app` at `127.0.0.1:8000` with reload off, and defaults `CREWAI_TELEMETRY_OPT_OUT` to `true`. Startup marks any leftover `researching`, `evaluating`, or `recommending` run as `failed` with the message "The process restarted before this run finished." It does not mark that run accepted.

Step 1 started that command. The log line was `Uvicorn running on http://127.0.0.1:8000`. `lsof` showed `127.0.0.1:8000 (LISTEN)`. This pass started it again. The application log line was `startup host=127.0.0.1 port=8000 telemetry_opt_out=true crewai_tracing=false`, followed by the Uvicorn startup line. `lsof` again showed `127.0.0.1:8000`.

Open:

- Recruiter: `http://127.0.0.1:8000/`
- Hiring manager: `http://127.0.0.1:8000/hiring-manager`
- Health: `http://127.0.0.1:8000/health`

## Shutdown

In a foreground terminal, Ctrl+C stops the process. The check in this step used `kill -TERM` on the background process. The process exited with status 143, and port 8000 was free afterward.

Shutdown does not write the final crew result. A run still in `researching`, `evaluating`, or `recommending` stays in that status until the next start, which marks it `failed`. The crew thread is a daemon thread and ends with the process.

## Verification

Commands and results from this step:

| Check | Result |
| --- | --- |
| `uv python find 3.13 --system` | `/Users/joeyrparker/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin/python3.13` |
| `uv venv --python 3.13` in a temp directory | CPython 3.13.18. Directory removed |
| `uv pip install --offline -r backend/requirements.txt --python .venv/bin/python` | Checked 4 packages |
| `uv pip install --offline -r backend/requirements.lock.txt --python .venv/bin/python` | Checked 151 packages |
| `.venv/bin/python -m pytest` | 16 passed in 0.82s. CrewAI deprecation warnings while building the crew object. No kickoff |
| `.venv/bin/python -m backend` | Started. Log: `Uvicorn running on http://127.0.0.1:8000` |
| `GET /health` | `200` `{"status":"ok"}` |
| `GET /`, `GET /hiring-manager`, `GET /css/app.css`, `GET /js/api.js` | `200` |
| `GET /api/runs/does-not-exist` | `404` |
| `lsof -nP -iTCP:8000 -sTCP:LISTEN` | `127.0.0.1:8000` |
| Request to the machine's other IPv4 address on port 8000 | Refused. curl exit 7 |
| `kill -TERM` | Process stopped. Port 8000 free. Exit status 143 |

`GET /health` does not prove the model, the search key, or a crew run. QA's browser pass remains simulated UI evidence. This pass did call the model once. The result is in `execution-results.md`: research failed with HTTP 429, and accept was not sent.

The startup checks from this pass, all at 2026-11-06T06:57:13Z unless noted:

| Check | Result |
| --- | --- |
| `.venv/bin/python -m pytest` | `17 passed` in 1.06s. Simulated. No kickoff |
| `.venv/bin/python -m backend` | Started. `startup host=127.0.0.1 port=8000 telemetry_opt_out=true crewai_tracing=false` |
| `GET /health`, `/`, `/hiring-manager`, `/css/app.css`, `/js/api.js` | `200` |
| `GET /api/runs/does-not-exist` | `404` |
| `lsof` | `127.0.0.1:8000` |
| `POST /api/runs` with the synthetic Platform engineer requisition | `202`, then `failed` at research. Live. Not a pass |
| Hiring-manager page for that run id | Browser showed failed at research. No ranking and no accept control. Live view of the failure |
| `kill -TERM` | `shutdown` at 2026-11-05 22:59:59 local. Exit status 143. Port 8000 free |

## Rollback

This rollback was not executed. It returns tracked files to a commit while keeping the uncommitted Deliver work recoverable and leaving local data on disk.

Verified on 2026-11-06:

- Git root: `recruitment-assistant` (`git rev-parse --show-toplevel`).
- HEAD: `cfa691f7a544d1dd28b7cdbcf2953f7eefa2ee3c`.
- Branch: `feature/deliver`. `main` is at the same commit.
- History under that baseline, newest first: `cfa691f` QA and Build docs, `7411231` integration, `9e21e7f` frontend, `87d8a62` backend, `09cac48` and `a7848bf` SAD, `fe248aa` MRD and PRD.
- Gitignored local data: `.env`, `.venv/`, `backend/runs/`, and the files in `project-context/2.build/logs/` other than `.gitkeep`.

Procedure:

1. Stop the process with Ctrl+C or `kill -TERM`. That stop was tested on 2026-11-05. It was not repeated for this write-up.
2. Do not use `git reset --hard`, `git clean`, or `git checkout --` on the working tree. Those discard uncommitted edits.
3. Save uncommitted work, including untracked files such as `Dockerfile`, `LESSONS.md`, and `project-context/3.deliver/`. Ignored local data is not included:

```bash
git stash push -u -m "uncommitted deliver work"
```

4. After that stash, the working tree matches `cfa691f` because HEAD is already that commit. Confirm with `git status` and `git rev-parse HEAD`. `.env`, `.venv/`, `backend/runs/`, and the log files stay on disk.
5. To inspect an older committed revision while the stash holds the Deliver work, `git switch --detach 7411231` (or another commit from the list above). Do not reset.
6. Reinstall pins only if that revision's lockfile differs from the environment: `uv pip install -r backend/requirements.lock.txt --python .venv/bin/python`. A restore onto another revision was not executed. The earlier offline check matched the current tree's lockfile to the current `.venv`.
7. Start with `.venv/bin/python -m backend` and request `GET /health`. That pair was tested on the current tree, before any rollback.
8. Return with `git switch feature/deliver` and `git stash pop`. Neither command was run for this document.

The next start marks an interrupted run `failed`. It does not accept it. Popping the stash does not delete `backend/runs/` or `.env`.

## Access control and localhost limitations

There is no login and no TLS. The control for this mini-project is the loopback bind plus the file permissions on `.env` and `backend/runs/`.

This step confirmed the listener was `127.0.0.1:8000` and that another address on the same machine was refused. Anyone who can open that loopback port while the process is running can submit a requisition, accept a draft, and read an accepted ranking. On a shared computer, other local accounts can do that.

`backend/__main__.py` is the bind. Changing it to all interfaces would expose the API on the network. This package keeps `127.0.0.1`.

Run files can hold names, profile URLs, and the ranking. They are gitignored. `.env` holds the model key and is gitignored. Logs and prompt traces are redacted and gitignored. The accepted ranking is a labeled draft the recruiter accepted. Contact decisions stay outside the product.

Search stays off while `SERPER_API_KEY` is empty. The Researcher is the only agent that can receive the search tools. Evaluator and Recommender have none.

This loopback process is the whole access design for the Tier-0 exercise. Accounts, SSO, TLS, and network segmentation are future work.

## Monitoring and logging

There is no APM, metrics scraper, or alerting. Logs are local files plus the process stderr.

| Signal | Location | Level | What it contains |
| --- | --- | --- | --- |
| Process log | stderr, and `project-context/2.build/logs/app.log` | `INFO` for startup, shutdown, crew start/end, and HTTP status below 400. `WARNING` for HTTP 4xx and `api_error`. `ERROR` for HTTP 5xx, unhandled request exceptions, and `task_failed` | Startup records the bind, `telemetry_opt_out`, and `crewai_tracing`. Request lines record method, path, status, and elapsed milliseconds. Error lines record status, error code, stage, or exception class. Crew lines record `run_id`, task name, tool names, `search_enabled` on research start, `source_elapsed_ms` on research end, and `error_class` |
| Uvicorn | stderr | Uvicorn's own info lines | Server start and its access lines. The application file is the one to read for the fields above |
| Task log | `project-context/2.build/logs/trace.jsonl` | One JSON object per event | `task_start`, `task_end`, and `task_failed`, passed through `backend/redact.py` |
| Prompt trace | `project-context/2.build/logs/prompt-{run_id}.json` | Written once before kickoff | Model name, temperature `0.2`, `max_tokens` `4096`, task text, and the requisition text plus pasted leads. This file is the prompt record. It is not the request log |
| Run record | `backend/runs/{run_id}/run.json` and `recommendation.md` | n/a | Status, requisition, candidates, evaluations, ranking, and the stored error |

`BACKEND_LOG_DIR` overrides the log directory. Unset, it is `project-context/2.build/logs`. That directory is gitignored except `.gitkeep`.

Request logs do not include the body, query string, headers, pasted leads, or secret values. `backend/redact.py` removes environment values whose names look like keys, `sk-` tokens, bearer tokens, and `li_at` strings before `trace.jsonl` and prompt files are stored. `GET /health` does not write a prompt file and does not call the model.

On this pass, `app.log` for run `9481a8b0-1e3c-4c9f-8e67-cedbe696e768` had the POST and the research `task_failed` line. It did not contain `sam.rivera@example.test`. The prompt file did contain that synthetic lead.

### CrewAI tracing

Leave tracing off. It is off by default.

`CREWAI_TELEMETRY_OPT_OUT` and `CREWAI_TRACING_ENABLED` are different switches. Telemetry opt-out stays `true`. Tracing is CrewAI 1.15.36's execution trace (`crewai/execution.py` stops that path when `CREWAI_TRACING_ENABLED` is `false` or `0`). `backend/crew.py` imports CrewAI, which loads `.env`, and then sets `CREWAI_TRACING_ENABLED` to `false` only if it is still unset. The crew is not constructed with `tracing=True`.

To turn tracing on for one operator machine, set `CREWAI_TRACING_ENABLED=true` in the uncommitted `.env` and restart `.venv/bin/python -m backend`. CrewAI can then record the run, including prompts and tool results, and its listener can send that trace to CrewAI. Do not commit the changed `.env`. Set the variable back to `false`, or run `crewai traces disable`, to turn it off again. This pass started the server with `CREWAI_TRACING_ENABLED=false`. The startup line said `crewai_tracing=false`.

`CREWAI_TELEMETRY_OPT_OUT=true` does not stop CrewAI from creating a local SQLite file when the crew object is built. That file is a library side effect, not an application metrics pipeline.

## Troubleshooting

| What you see | What it means |
| --- | --- |
| `python3` is 3.14, or `python3.13` is not found | Use `uv python find 3.13 --system` and `uv venv --python 3.13`. CrewAI 1.15.36 does not install on 3.14 |
| `No module named pip` from `.venv/bin/python -m pip` | This `.venv` was installed with uv and has no pip module. Use `uv pip install` |
| `Address already in use` | Something is already listening on `127.0.0.1:8000`. Stop that process before starting another |
| Browser cannot reach the API from a file opened on disk | Use `http://127.0.0.1:8000/`. The pages are served by this process |
| `ModuleNotFoundError: backend` | The working directory was not `recruitment-assistant` |
| Research ends `failed` with "No pasted leads and search is off" | Expected when both the paste and `SERPER_API_KEY` are empty. The model is not called |
| A pasted-lead run fails after the crew starts | The run stays `failed` and unaccepted. Read `error.stage` and `error.message` on the run. On 2026-11-05 the provider text was HTTP 429 `credit_balance_exhausted` ("You have no credits remaining"). Adding credits is an account action. The key value is not in the log line; `app.log` records `error_class` only |
| `409` `run_in_progress` | One crew run at a time. Wait until it is `draft`, `failed`, `accepted`, or `discarded` |
| A run says the process restarted | The previous process stopped mid-run. The new process marked it `failed` |
| `GET /health` is ok and a real shortlist never appears | Health does not call the model. A 429 during research never reaches draft |
| Crew config test: `unable to open database file` | CrewAI could not create its local SQLite file. On this machine the same test passed when that write was allowed. The other tests do not build the crew object |
| `docker: command not found` | The image was not part of the tested procedure. Use the virtualenv commands |
| Startup line says `crewai_tracing=false` | Expected. Tracing is off unless `CREWAI_TRACING_ENABLED=true` was set before the crew module defaulted it |

## Future work

Left outside this Tier-0 closeout:

- CI for lint, unit test, and build.
- `project-context/3.deliver/user-guide.md`.
- `@security.eng` and `security.md` before any host other than this loopback process.
- A built container. `docker` was not run.
- APM, autoscaling, multi-region hosting, and infrastructure-as-code.

Successful live CrewAI execution remains unverified because API credits were unavailable. This exercise will not purchase credits or retry the model. Simulated tests do not fill that gap. Search-on sourcing was not run.

## Sources

- `project-context/1.define/prd.md` (Module 07 scope, no live deploy, F1–F6, out of scope)
- `project-context/1.define/sad.md` Section 5 (local process, `127.0.0.1:8000`, health, logs) and Section 8 (localhost, secrets)
- `project-context/2.build/qa.md` (simulated MVP pass)
- `project-context/3.deliver/execution-results.md` (this pass: pytest, startup, and the failed live call)
- `LESSONS.md`
- `project-context/2.build/backend.md` (entry, pins, API, trace paths)
- `project-context/2.build/frontend.md` and `project-context/2.build/integration.md` (pages served by this process)
- `.env.example`
- `backend/requirements.txt`, `backend/requirements.lock.txt`, `backend/__main__.py`, `backend/app.py`, `backend/trace.py`, `backend/store.py`, `backend/redact.py`
- `.cursor/agents/devops-eng.md`
- `.cursor/rules/delivery-workflow.mdc`
- `.cursor/rules/adapter-crewai.mdc` and `.cursor/rules/adapter-registry.mdc`
- `aamad.config.example.yml` read as a schema sample. `aamad.config.yml` is absent
- `project-context/2.build/security.md` is absent
- `project-context/2.build/setup.md` (verified setup; untested clean-machine install steps are listed there)

## Assumptions

- The operator accepted the missing `security.md` for this local Tier-0 exercise. `aamad.config.yml` is absent, so its `security.require_security_assessment` flag is not loaded. `aamad.config.example.yml` would set that flag to true if it were copied. It was not copied and is not project configuration.
- `AAMAD_TARGET_RUNTIME` is configured in `.env`. The value was not printed. It resolves to `crewai` from the SAD, the PRD, `.env.example`, and `.cursor/rules/adapter-registry.mdc`.
- The SAD's smallest host is one local process. The `Dockerfile` records that process for a later image build. This step does not switch the host to a container or a cloud service.
- `.env` is present. This pass classified each name as absent, empty, placeholder, or configured. Values were not printed and `.env` was not written. No secret value was written into this file, the Dockerfile, or `.dockerignore`.
- `APP_NAME` and `APP_ENV` remain in `.env.example` even though the current process does not read them. `BACKEND_RUNS_DIR` and `BACKEND_LOG_DIR` are code overrides and were left out of `.env.example`.
- The live call failed because the provider reported no credits. The operator will not purchase credits. Successful live CrewAI execution remains unverified. Search-on sourcing was not run. Simulated results are not evidence of live model behavior.
- README now points at this runbook and at the execution record. The fresh-virtualenv `pip` lines in the README were not executed in this pass.
- Application edits in this pass are logging only: startup, request metadata, crew events, and error class or code. Request lines do not store bodies.

## Open Questions

- Carried from the PRD and SAD: time-to-source target, match-accuracy percentage, satisfaction average, retention of run files, NYC or EU employment use, and whether a degree may outweigh skills.
- Successful live CrewAI execution remains unverified because API credits were unavailable. The failed attempt is in `execution-results.md`. This exercise will not retry it.
- Should `@security.eng` run before any host other than this loopback process? The example config asks for an assessment. The PRD module map does not assign that persona. This step records the operator's acceptance for the local exercise only.
- When Docker is available, does `docker build` from `backend/requirements.lock.txt` succeed on that engine? It was not run here.
- No release version has been assigned.

## Audit

- **Timestamp**: 2026-11-05T22:16:18-08:00
- **Persona id**: `devops-eng`
- **Action**: `prepare-release`, `define-deploy`, `document-deploy`
- AAMAD_TARGET_RUNTIME: crewai
- **Runtime warning**: `AAMAD_TARGET_RUNTIME` was unset in this shell and `aamad.config.yml` was not present. Resolved to `crewai` from the SAD, the PRD, `.env.example`, and `.cursor/rules/adapter-registry.mdc`.
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed and were not set. The application crew was not kicked off. No live model run.
- **LLM controls recorded for the application**: model name from `OPENAI_MODEL`, default `gpt-4o`; temperature `0.2`; max_tokens `4096`. Those controls were not used in this step.
- **Package**: `Dockerfile` and `.dockerignore`. Entry point `python -m backend`. Dependency file `backend/requirements.lock.txt`. Direct pins remain `backend/requirements.txt`.
- **Command results**: uv interpreter find, temporary venv create, offline dependency check, `16 passed`, process start, health `{"status":"ok"}`, page and static `200`, unknown run `404`, bind `127.0.0.1:8000`, other-address refusal, SIGTERM shutdown. Details are in Verification.
- **Untested**: `docker build`, `docker run`, the image `HEALTHCHECK`, `cp .env.example .env`, a network install into an empty venv, `POST /api/runs`, a live model call, and rollback onto a previous tree.
- **Security gate**: `security.md` absent. Accepted for this local Tier-0 exercise. Recorded under Assumptions.
- **Deploy status**: Step 1 only. The verification process was stopped. Deliver is not complete. No cloud deploy.
- **Prompt Trace**: The operator asked for Module 07 Step 1, deployment packaging and `deploy.md`, limited to the existing Python 3.13, CrewAI, FastAPI, and localhost app. The request named release scope, hosting, an environment matrix without secret values, install, start, stop, verification, rollback, access control, localhost limits, existing monitoring, troubleshooting, sources, assumptions, open questions, and audit. It asked to carry the live-model gap, record the missing `security.md` as an accepted gap, validate commands where possible, and leave Deliver incomplete with no commit and no cloud deploy. System-prompt text is omitted.
- **Output path**: `project-context/3.deliver/deploy.md`
- **Handoff**: CI scaffolding and `project-context/3.deliver/user-guide.md` remain. A live model run is still open.

## Audit

- **Timestamp**: 2026-11-05T23:00:49-08:00
- **Persona id**: `devops-eng`
- **Action**: monitoring, execution record, lessons, and runbook update
- AAMAD_TARGET_RUNTIME: crewai
- **Runtime warning**: `aamad.config.yml` was not present. Resolved runtime remains `crewai`.
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed. The application crew was kicked off once. Prompt trace recorded `gpt-4o`, temperature `0.2`, `max_tokens` `4096`. The provider returned 429 before a ranking.
- **Command results**: pytest `17 passed` in 1.06s. Server start, health and page `200`, unknown run `404`, bind `127.0.0.1:8000`, live `POST /api/runs` then `failed`, hiring-manager page showed that failure, SIGTERM exit 143. Details are in `execution-results.md`.
- **Logging**: `app.log` and stderr. Levels `INFO`, `WARNING`, and `ERROR`. Request metadata only. `CREWAI_TRACING_ENABLED` left false.
- **Security gate**: `security.md` absent. Accepted for this local Tier-0 exercise. Recorded under Assumptions.
- **Deploy status**: Not complete. The live draft, accept, and hiring-manager ranking did not pass. No cloud deploy. No commit.
- **Prompt Trace**: The operator asked to finish the remaining Module 07 work in one pass on `feature/deliver`: logging, a live crew attempt if a key existed, lessons, README and runbook updates, and validation, without staging secrets or committing. System-prompt text is omitted.
- **Output path**: `project-context/3.deliver/deploy.md`
- **Handoff**: The later audit records the Tier-0 closeout. `security.md` was still an accepted gap.

### 2026-11-06T05:59:47-08:00

- **Persona id**: `devops-eng`
- **Action**: correct the repository and rollback record, and close local delivery on simulated evidence
- AAMAD_TARGET_RUNTIME: crewai
- **Repository**: Git root is `recruitment-assistant`. Committed baseline is `cfa691f`. Rollback was documented and not executed.
- **Status**: Local delivery and simulated validation complete. Successful live CrewAI execution remains unverified because API credits were unavailable.
- **What stayed**: the failed live attempt in `execution-results.md`. No model retry. No commit. CI, the user guide, and Docker were not added.
- **Prompt Trace**: The operator corrected the course hat names, the git baseline, and the decision not to purchase API credits. System-prompt text is omitted.
