# WardPulse progress log

**Every agent: update this file after each task, then commit it (`docs: update progress`).**
Keep it short and factual. This file is how the next agent knows where things stand.

Status values: `TODO`, `IN PROGRESS`, `DONE`, `BLOCKED`.

**Next recommended prompt: P1 (Lane A: Simulator) or P2 (Lane B: Engine A)** (update this line after every task)

**For a new Claude chat reading this file:** use the table, the contract tests and the Change log to see exactly where the project stands, then give the human the next prompt(s) from `docs/AGENT_PROMPTS.md` (see `docs/CLAUDE_TAKEOVER.md`). Prompts can be given as short launcher lines.

Project-level status: Round 1 form submitted and the objective and goals presentation is done. Round 2 build is in progress (about 24 hours from 14 Oct 2026).

## Work packages

| ID | Package | Status | Owner | Notes for the next agent |
|----|---------|--------|-------|--------------------------|
| P0 | Bootstrap: skeleton, requirements, stubs, README, smoke tests | DONE | Agent | Repo skeleton, packages, venv, requirements, stubs, smoke tests (6 passed), run scripts, README |
| P1 | Simulator: 20-bed ward, 3 demo stories, sim clock | TODO | | |
| P2 | Engine A: features, safety, risk (rules), NEWS2, safety-rules.md | TODO | | |
| P3 | Engine B: freshness, tasks, prioritizer, pipeline | TODO | | |
| P4 | Backend: database, API, sim clock loop, SSE, audit | TODO | | |
| P5 | Frontend: nurse console (mock data first, then real API) | TODO | | |
| P6 | Integration: run everything together, verify 3 stories | TODO | | |
| P7 | Evaluation: replay, metrics, NEWS2 vs WardPulse | TODO | | |
| P8 | LightGBM risk model (optional) | TODO | | |
| P9 | Polish: demo script, README, fresh-clone test, presentation notes | TODO | | |

## Contract tests (from docs/contracts.md section 10)

| # | Test | Status |
|---|------|--------|
| 1 | Story 1: Bed 3 RR 22 no card, Bed 7 RR 22 active card | TODO |
| 2 | Story 2: stale BP gives repeat_bp, not page_doctor | TODO |
| 3 | Story 3: crash appears in emergency while active still has 2 | TODO |
| 4 | Budget: 10 abnormal patients, len(active) <= k_budget | TODO |
| 5 | Naive mode shows more alerts_shown than WardPulse | TODO |
| 6 | Aging: queued priority rises with waiting time | TODO |
| 7 | Escalation: ignored active task becomes escalated | TODO |
| 8 | Missing data: all-None vitals do not crash the engine | TODO |
| 9 | Determinism: same seed gives identical ward and results | TODO |
| 10 | Safety: baseline never suppresses a red-line breach | TODO |

## Decisions log

- 2026-10-14: `schemas.py` lives in `backend/shared/` (not `app/`) so the engine stays independent of the web layer.
- 2026-10-14: Naive comparator is real NEWS2 (aggregate at or above threshold, or any single parameter at the maximum score), SpO2 Scale 1 for everyone by default.
- 2026-10-14: LightGBM is optional and only added after the rules version works end to end.
- 2026-10-14: Frontend is React + Vite + TypeScript + Tailwind, built first against mock data matching `schemas.py`.

## Open questions and blockers

- (none yet)

## Known risks to watch

- `schemas.py` verified in P0: executes cleanly with 0 errors.
- Public dataset access (PhysioNet / MIMIC) not verified (P7 checks first).
- Safety limits and card wording need clinician or nursing-student review before the demo.

## Change log (newest first)

- 2026-10-14 | P0 | Bootstrap completed: repo structure with __init__.py files, requirements.txt installed in backend/.venv, verified schemas.py (no fixes needed), DEFAULT_CONFIG in engine/config.py, stubs for pipeline, news2, ward simulator, FastAPI app with /health and CORS, test_schemas_smoke.py (6 passed, 0 failed), README.md, run_backend scripts | backend/requirements.txt, backend/shared/__init__.py, backend/app/__init__.py, backend/app/api/__init__.py, backend/app/db/__init__.py, backend/engine/__init__.py, backend/engine/config.py, backend/engine/pipeline.py, backend/engine/news2.py, backend/simulator/__init__.py, backend/simulator/ward.py, backend/evaluation/__init__.py, backend/ml/__init__.py, backend/tests/__init__.py, backend/tests/test_schemas_smoke.py, backend/app/main.py, README.md, scripts/run_backend.sh, scripts/run_backend.ps1, .gitignore, docs/PROGRESS.md | 6 passed, 0 failed | None | Next: P1 (Lane A: Simulator) or P2 (Lane B: Engine A)
- 2026-10-14 | docs | Handoff files created (AGENTS.md, PROJECT_CONTEXT.md, PROGRESS.md, AGENT_PROMPTS.md, CLAUDE_TAKEOVER.md), plus contracts.md, schemas.py, .gitignore | no code run yet | next: P0
