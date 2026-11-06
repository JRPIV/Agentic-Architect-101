# Setup: Recruitment Assistant

This file records the local setup that was verified for the Tier-0 exercise. `@project.mgr` was not assigned in the PRD module map, so Build left this file unwritten. It was added during Deliver from commands that had already been run. It does not describe a new install.

## Verified environment

Checked from `recruitment-assistant` on 2026-11-05 and 2026-11-06.

| Item | Verified result |
| --- | --- |
| Git root | This directory. `git rev-parse --show-toplevel` is the application repository, not the parent `Agentic Architect 101` folder |
| Committed baseline | `cfa691f` (`docs: Complete Tier-0 QA and Build documentation`). `feature/deliver` and `main` both point at that commit |
| Interpreter | `.venv/bin/python` is Python 3.13.18. Confirmed again on 2026-11-06 |
| Why not the system `python3` | That interpreter is 3.14. CrewAI 1.15.36 requires Python `>=3.10,<3.14` |
| Virtualenv tool | uv 0.13.7. `uv python find 3.13 --system` returned the uv-managed CPython 3.13. A temporary `uv venv --python 3.13` reported 3.13.18 and was removed. The project `.venv` was left in place |
| Direct dependencies | `uv pip install --offline -r backend/requirements.txt --python .venv/bin/python` checked 4 packages: `crewai[tools]==1.15.36`, `fastapi==0.162.0`, `uvicorn==0.54.0`, `pytest==9.2.0` |
| Lockfile | `uv pip install --offline -r backend/requirements.lock.txt --python .venv/bin/python` checked 151 packages |
| Pip module | `.venv/bin/python -m pip` fails with `No module named pip`. The installer used here is `uv pip` |
| `.env` | Present before Deliver. It was not overwritten. Names were classified without printing values. `OPENAI_API_KEY` was configured. `SERPER_API_KEY` was absent. `CREWAI_TRACING_ENABLED` was absent until the server process set it to `false` |
| Start | `.venv/bin/python -m backend` listened on `127.0.0.1:8000` |
| Tests | `.venv/bin/python -m pytest`: `17 passed` in 1.06s after the logging edits. The tests stub the crew. They do not prove live model behavior |
| Shutdown | `kill -TERM` exited 143 and freed port 8000 |

`backend/__main__.py` sets `CREWAI_TELEMETRY_OPT_OUT` to `true` when it is unset. `backend/crew.py` sets `CREWAI_TRACING_ENABLED` to `false` when it is still unset after CrewAI loads `.env`.

## Commands for a machine that already matches this tree

From `recruitment-assistant`, when `.venv` and `.env` are already present:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m backend
```

Health is `GET http://127.0.0.1:8000/health`. The recruiter page is `/`. The hiring-manager page is `/hiring-manager`.

## Installation steps not tested

These steps are the ones a clean machine would need. They were not run against an empty project directory.

- `uv venv --python 3.13 .venv` inside this project. The 3.13.18 check used a temporary directory, which was deleted.
- A network install into an empty virtualenv. The dependency check was `uv pip install --offline` against the existing `.venv`.
- `cp .env.example .env`. `.env` was already present and was not replaced.
- `python3.13 -m venv .venv` and `.venv/bin/python -m pip install`. This `.venv` has no pip module.
- `aamad` was not installed into `.venv`. The later `aamad validate` command used `/Library/Frameworks/Python.framework/Versions/3.14/bin/aamad`.
- `docker build` and `docker run`. `docker` was not used.

Do not bind `0.0.0.0`. Do not add `LI_AT`. Leave `SERPER_API_KEY` empty for pasted leads. Leave `CREWAI_TRACING_ENABLED` false.

## Sources

- `project-context/3.deliver/deploy.md` (install, start, and the offline dependency check)
- `project-context/3.deliver/execution-results.md` (pytest, startup, and the failed live call)
- `project-context/2.build/backend.md` (Python requirement and pins)
- `backend/requirements.txt` and `backend/requirements.lock.txt`
- `.env.example`
- `.gitignore`
- `git rev-parse` and `git log` on 2026-11-06
- `.venv/bin/python --version` on 2026-11-06

## Assumptions

- AAMAD_TARGET_RUNTIME: crewai. `.env` has the name configured. The value was not printed. `aamad.config.yml` is absent.
- The existing `.venv` still matches the lockfile because the offline check reported the packages as checked. A clean reinstall was not performed.
- `security.md` is still absent. That gap is accepted for this localhost exercise.

## Open Questions

- None for the verified local start. A fresh-machine install remains untested, as listed above.
- Successful live CrewAI execution remains unverified because API credits were unavailable. This exercise will not purchase credits or retry the model.

## Audit

- **Timestamp**: 2026-11-06T05:59:47-08:00
- **Persona id**: `devops-eng`
- **Action**: record the verified local setup after Build left this file unwritten
- AAMAD_TARGET_RUNTIME: crewai
- **Model**: Grok 4.7, Cursor agent session. Temperature and max_tokens were not exposed. No model call was made while writing this file.
- **Prompt Trace**: The operator asked for `setup.md` from the verified existing setup, with untested install steps identified, and for the Deliver closeout to keep the failed live attempt separate from simulated validation. System-prompt text is omitted.
- **Output path**: `project-context/2.build/setup.md`
