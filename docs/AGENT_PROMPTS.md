# Agent prompts (copy and paste one block per agent task)

How to use:
1. Open a new agent session in the repo, paste ONE prompt block below, let it finish.
2. Check the result (the "Done when" lines), make sure it committed and updated `docs/PROGRESS.md`.
3. Run prompts in the order and lanes below. Lanes can run at the same time in separate agent sessions.

```
P0  (first, alone, about 1h)
 |
 +-- Lane A: P1 simulator ----------------------+
 +-- Lane B: P2 engine A -> P3 engine B --------+--> P6 integration --> P7 evaluation --> P8 LightGBM (optional)
 +-- Lane C: P4 backend API + DB ---------------+                                   \
 +-- Lane D: P5 frontend (mock data first) -----+                                    --> P9 polish and demo
```

Every prompt starts with the same "read first" block, so a brand-new agent with no memory can do the work.

---

## P0 Bootstrap (run first, alone)

```
You are a senior engineer setting up the WardPulse hackathon repo. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md, backend/shared/schemas.py, docs/PROGRESS.md. (If AGENTS.md or PROJECT_CONTEXT.md is missing, tell me and stop.)

Your scope: repo skeleton only. Do not implement real logic.

Tasks:
1. Create the folders with empty __init__.py files where Python packages are needed: backend/{shared,app,app/api,app/db,engine,simulator,evaluation,ml,tests}, plus data/sample, data/raw (with a .gitkeep), scripts. Do NOT create the frontend folder.
2. backend/requirements.txt with: fastapi, uvicorn[standard], pydantic>=2, sqlalchemy>=2, sse-starlette, numpy, pandas, scikit-learn, lightgbm, pytest, httpx.
3. Create a virtual environment OUTSIDE version control (backend/.venv is git-ignored), install requirements, and verify: `cd backend && python -c "from shared.schemas import *; print('schemas ok')"`.
   backend/shared/schemas.py was written without ever being executed. If it has an error, make the smallest possible fix, commit it separately with prefix `contract:`, and describe the fix in docs/PROGRESS.md under Decisions log. Do not otherwise change it.
4. backend/engine/config.py: `from shared.schemas import EngineConfig` and `DEFAULT_CONFIG = EngineConfig()`.
5. Stubs with the EXACT signatures from docs/contracts.md section 5 and 6, returning valid empty results so every other module can import them:
   - backend/engine/pipeline.py: evaluate_ward(...) returning a valid WardEvaluation (mode wardpulse, budget_k from config, empty lists).
   - backend/engine/news2.py: evaluate_ward_news2(...) same, mode news2, budget_k None.
   - backend/simulator/ward.py: build_ward(seed=42) returning ([], []); class Simulator with advance, reset (no-ops).
6. backend/app/main.py: FastAPI app with GET /health returning {"status": "ok"} and CORS allowing http://localhost:5173.
7. backend/tests/test_schemas_smoke.py: tests that (a) valid Patient, VitalsIn, Task, TasksResponse build, (b) sbp < dbp raises, (c) VitalsIn with no measurement raises, (d) TasksResponse.alerts_shown equals len(emergency)+len(active), (e) the stubs return valid WardEvaluation objects.
8. README.md (the repo README is empty): what WardPulse is in 5 lines, the "decision support, not diagnosis" note, quick start (backend: create venv, install, `cd backend && uvicorn app.main:app --reload --port 8000`; frontend: placeholder "added in P5"), repo structure, how to run tests (`cd backend && pytest`), team workflow (small commits with prefixes), and links to docs/.
9. scripts/run_backend.sh and scripts/run_backend.ps1 that start the backend.

Done when: `cd backend && pytest` passes, `uvicorn app.main:app` starts and /health works.
Finish: update docs/PROGRESS.md (P0 DONE, notes), check `git status` for stray files, commit in logical commits (`chore:` for skeleton, `docs:` for README, `api:` for main.py, `contract:` only if you fixed schemas.py), then push.
```

---

## P1 Simulator (Lane A)

```
You are building the ward simulator for WardPulse. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md (sections 1, 2, 6), backend/shared/schemas.py, docs/PROGRESS.md.

Your scope: ONLY backend/simulator/ and backend/tests/test_simulator.py. Do not touch the engine, API or schemas.

Build, matching the contract in docs/contracts.md section 6:
- backend/simulator/ward.py: `build_ward(seed=42) -> (list[Patient], list[VitalsReading])` creating 20 patients (beds 1 to 20, anonymous display names like "Bed 7", varied ages) plus about 24 hours of prior history ending at SIM_START. Define SIM_START as a fixed constant (for example datetime(2026, 10, 20, 6, 0)). Use random.Random(seed) only, so results are identical for the same seed.
- Most beds get readings every 4 to 6 hours with small time jitter and realistic noise. At least 3 scheduled readings across the ward are deliberately missed. Occasionally a single vital is None in a reading.
- backend/simulator/scenarios.py: the fixed bed roles:
  * Bed 3: COPD, chronic RR 21 to 23, SpO2 about 90 to 92, stable for the whole history.
  * Bed 7: post-op, RR 14, 14, 15, 17, then 22 by about SIM_START + 1h, pulse rising gently.
  * Bed 4: borderline and falling SBP earlier (about 128 down to 112); last BP taken about 4h before SIM_START so it is 7h old at SIM_START + 3h, while other vitals are retaken about 1h before.
  * Bed 12: stable until SIM_START + 5h, then a crash reading: SBP about 78, HR about 135, SpO2 about 86.
  * At least four more beds (a mix of COPD and cardiac) with chronic-abnormal but stable vitals that a fixed-threshold score would flag, so naive mode shows many cards.
  * All other beds: stable, normal.
- backend/simulator/clock.py: `class Simulator` with `__init__(seed=42)`, `advance(to: datetime) -> list[VitalsIn]` returning only readings due between the last advance and `to` (scenario events included), and `reset()`. It keeps its own internal time cursor; it never calls datetime.now().
- Put the exact scripted timeline in a docstring at the top of scenarios.py and also write it to docs/demo-script.md (sim times, what the audience should see, which cards should appear). The sim time of each story must be clear.

Tests (backend/tests/test_simulator.py): 20 patients; determinism (same seed gives identical output, different seed differs); Bed 3 history RR all between 20 and 24; Bed 7 latest RR in history or at SIM_START + 1h equals 22; Bed 4 last SBP reading is at least 7h before SIM_START + 3h; at least 3 missed scheduled readings; the Bed 12 crash reading appears only after SIM_START + 5h; advance() never returns readings before the previous cursor; all outputs validate against shared.schemas.

Done when: `cd backend && pytest tests/test_simulator.py` passes.
Finish: update docs/PROGRESS.md (P1 DONE, plus the story times for the next agent), `git status`, small commits with prefix `sim:` (docs commit for the demo script with `docs:`), push.
```

---

## P2 Engine A: features, safety, risk, NEWS2 (Lane B)

```
You are building the first half of the WardPulse engine. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md (sections 1, 2, 4, 5), backend/shared/schemas.py, docs/PROGRESS.md.

Your scope: ONLY backend/engine/features.py, safety.py, risk.py, news2.py, backend/tests/test_engine_a.py, and docs/safety-rules.md. Pure logic: no web, database, file or clock access; time is passed in as `now`. Do not edit schemas.py. (You may add one clarifying sentence to docs/contracts.md section 5 about the NEWS2 alert rule below, with a `docs:` commit.)

Build:
1. news2.py: `news2_components(reading, patient, config) -> dict` and `news2_score(...) -> int` implementing the standard NEWS2 chart (Royal College of Physicians): respiratory rate, SpO2 (Scale 1 by default; Scale 2 only if config.news2_spo2_scale2_for_copd and the patient has COPD), air or oxygen, systolic BP, pulse, consciousness (ACVPU), temperature. Treat a missing vital as 0 points and record it as missing. VERIFY every band against an official NEWS2 source and cite it in docs/safety-rules.md. Naive alert rule: raise an alert if the aggregate score >= config.news2_alert_threshold OR any single parameter scores 3. Also implement evaluate_ward_news2(...) with the exact signature in contracts.md: every patient meeting the alert rule becomes a Task of type news2_alert in `active` (no budget, budget_k None, sorted by score), fill news2_score in assessments, build the WardOverview.
2. features.py: per patient and per vital: personal baseline from readings within config.baseline_window_hours, excluding the latest config.baseline_exclude_latest reading(s), using median and MAD with a floor on the spread; blend toward a condition-based prior (document your priors for copd, post_op, cardiac and a general adult in safety-rules.md) with weight config.prior_blend when there are fewer than config.min_baseline_readings readings; deviation score vs baseline; trend per hour; shock index (hr / sbp); age in hours of each vital; stale detection input. Return a clear typed structure (a small dataclass or Pydantic model local to the engine).
3. safety.py: absolute red lines using the NEWS2 chart as the source (any single parameter at the maximum score, or aggregate at a high-risk level) and `is_crash(...)`. A personal baseline may reduce a false alarm only inside safe limits and must never hide a red-line breach. The Story 3 vitals (SBP about 78, HR about 135, SpO2 about 86) MUST be crash.
4. risk.py: transparent rule-based `risk_score` (0 to 1) combining NEWS2-style severity, baseline deviation, trends and shock index, with a hook `ml_score: float | None` that is blended in later if provided. Map to RiskTier using config cutoffs. Produce short plain-language `reasons` with real numbers, for example "RR 14 -> 22 over 5h".
5. docs/safety-rules.md: where every limit and prior comes from, the crash definition, the NEWS2 citation, and a clear note that these need clinician or nursing-student review.

Tests (backend/tests/test_engine_a.py, hand-built fixtures, no simulator): NEWS2 known examples; missing vitals handled; COPD patient at their own baseline (RR 22, SpO2 91) has LOW or MEDIUM risk while a post-op patient going RR 14 -> 17 -> 22 with rising pulse is HIGH; the crash vitals are crash; a baseline never suppresses a red-line breach; all-None readings do not raise; a patient with one reading (cold start) still gets a sensible result.

Done when: `cd backend && pytest tests/test_engine_a.py` passes.
Finish: update docs/PROGRESS.md (P2 DONE, plus the function names and any decisions P3 needs to know), `git status`, small commits with prefix `engine:`, push.
```

---

## P3 Engine B: freshness, tasks, prioritizer, pipeline (Lane B, after P2)

```
You are building the second half of the WardPulse engine. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md (sections 1, 2, 4, 5, 10), backend/shared/schemas.py, docs/safety-rules.md, docs/PROGRESS.md. P2 must be DONE (features, safety, risk, news2 exist); if not, stop and say so.

Your scope: ONLY backend/engine/freshness.py, tasks.py, prioritizer.py, pipeline.py, backend/tests/test_engine_b.py and backend/tests/fixtures.py. Pure logic, time passed in as `now`. Do not edit schemas.py or the P2 files except for tiny bug fixes (note them in PROGRESS.md).

Build:
1. freshness.py: next_vitals_due per patient from the risk tier (config.vitals_due_hours); stale vitals when age > config.stale_after_factor x due interval; hours_since_last_vitals; flags for borderline-and-stale.
2. tasks.py: turn each PatientAssessment into candidate Tasks using ONLY the closed TaskType set and TASK_TITLES from schemas.py, with a one-line reason built from real numbers (for example "RR 14 -> 22 over 5h; BP not taken for 7h"):
   - fresh and high risk -> page_doctor (plus sit_upright or check_oxygen_cannula where the vitals suggest it, for example low oxygen on supplemental oxygen -> check_oxygen_cannula)
   - borderline risk and stale data -> repeat_* for the stale vital (or full_vitals_recheck if everything is old); NEVER page_doctor from stale data alone
   - crash -> page_doctor with emergency=True
   - Set target_vital from TASK_TARGET_VITAL.
3. prioritizer.py: priority = urgency from risk plus config.aging_per_hour x hours waiting; at most config.k_budget tasks `active`, the rest `queued` in priority order; crash tasks go to `emergency` outside the budget; a task not completed within config.escalation_after_minutes gets escalated=True and a priority boost. Task identity is (patient_id, type): while the condition persists keep the same id and created_at from previous_tasks (this is what makes aging work); drop tasks whose condition cleared; ignore previous tasks that are done or dismissed unless the condition worsens materially. Task ids for new tasks must be assigned deterministically (for example max existing id + 1).
4. pipeline.py: `evaluate_ward(patients, vitals, now, config, previous_tasks=None) -> WardEvaluation` wiring features -> safety + risk -> freshness -> tasks -> prioritizer, filling assessments (including news2_score) and the WardOverview (map tier to WardStatus; data_stale; has_open_task). Replace the P0 stub.
5. tests/fixtures.py with small hand-built patients and readings for the three stories, plus a 10-abnormal-patients ward. Do NOT import the simulator.

Tests (backend/tests/test_engine_b.py), exactly the contract tests 1 to 8 in docs/contracts.md section 10 (and 10 if not already covered in P2): Story 1, Story 2, Story 3 (emergency while active holds 2), budget, naive vs WardPulse alerts_shown, aging, escalation, all-None vitals.

Done when: `cd backend && pytest` passes with the engine tests green.
Finish: update docs/PROGRESS.md (P3 DONE, tick the contract tests that pass, list anything the API agent must know), `git status`, small commits with prefix `engine:`, push.
```

---

## P4 Backend: database, API, clock loop, SSE (Lane C)

```
You are building the WardPulse backend service. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md (all sections, especially 8 and 9), backend/shared/schemas.py, docs/PROGRESS.md.

Your scope: ONLY backend/app/ and backend/tests/test_api.py. The engine and simulator may still be stubs or in progress: call them only through their contract signatures (engine.pipeline.evaluate_ward, engine.news2.evaluate_ward_news2, simulator.clock.Simulator, simulator.ward.build_ward) so real implementations drop in later. Do not edit schemas.py, the engine or the simulator.

Build:
1. app/db/: SQLAlchemy 2 models for the tables in contracts.md section 9 (SQLite file at backend/wardpulse.db, git-ignored), a session helper, and `python -m app.db.seed` that resets the DB and loads patients and history from build_ward(seed). If build_ward returns empty (stub), seed 3 tiny placeholder patients so the API still works.
2. app/api/: every endpoint in contracts.md section 8 with the exact request and response models from shared.schemas: GET /health, /ward, /patients/{id}, /tasks?mode=wardpulse|news2, POST /vitals, POST /tasks/{id}/done, POST /tasks/{id}/not-useful, GET /sim/state, POST /sim/control, GET /stream (server-sent events using sse-starlette), GET /eval/results (read backend/evaluation/results.json if it exists, else 404 with a clear message), GET /audit.
3. A re-evaluation service: load patients and vitals from the DB, call evaluate_ward with config.DEFAULT_CONFIG and the persisted open tasks as previous_tasks, persist the resulting tasks (create, update, close), and write audit entries (task_created, task_done, task_not_useful, vitals_entered, crash_bypass). Naive mode is computed on the fly with evaluate_ward_news2 and previous_tasks=None, never persisted. Marking a task done or not-useful changes its status and re-evaluates.
4. A simulation clock: an asyncio background task that, while running, advances sim_time by speed_minutes_per_second each real second, calls Simulator.advance(sim_time), stores new readings (source "sim"), re-evaluates, and emits StreamEvents (sim_tick each tick; tasks_updated and ward_updated when changed; emergency when a crash task appears). POST /sim/control handles play, pause, reset (reseed DB and restart the Simulator), set_speed.
5. POST /vitals: timestamp None means current sim_time; validate patient exists; store; re-evaluate; emit events.
6. CORS for http://localhost:5173. Clear error responses ({"detail": ...}).

Tests (backend/tests/test_api.py, FastAPI TestClient with a temporary database): health; ward returns 20 or placeholder beds; posting vitals returns a VitalsReading and triggers re-evaluation; done and not-useful change status and write audit and feedback rows; sim control changes SimState; both modes of /tasks return a valid TasksResponse; invalid vitals return 422.

Done when: `cd backend && pytest tests/test_api.py` passes and `uvicorn app.main:app --port 8000` serves /docs.
Finish: update docs/PROGRESS.md (P4 DONE, base URL, how to seed, anything the frontend needs), `git status`, small commits with prefix `api:`, push.
```

---

## P5 Frontend: nurse console (Lane D, starts immediately with mock data)

```
You are building the WardPulse nurse console. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md (sections 3, 4, 8), backend/shared/schemas.py, docs/PROGRESS.md.

Your scope: ONLY the frontend/ folder (create it). Stack: React + Vite + TypeScript + Tailwind CSS. Do not touch the backend. The backend may not be ready, so BUILD AGAINST MOCK DATA FIRST: put typed mock JSON that exactly matches the shapes in schemas.py in frontend/src/mock/, and a flag VITE_USE_MOCK=true (default true until the real API works) that swaps the API client. API base URL comes from VITE_API_URL (default http://localhost:8000). Write TypeScript types in frontend/src/types.ts that mirror shared/schemas.py exactly (same field names).

The product goal: an overloaded nurse sees only what matters. The design must be calm, clean and fast to read on a tablet or laptop, large touch targets, high contrast, not a wall of red.

Build:
1. Header: app name, "Decision support, not diagnosis" note, simulation clock (current sim time, play, pause, speed selector, reset) wired to /sim/state and /sim/control.
2. Mode toggle: "Naive AI (NEWS2)" vs "WardPulse". Switching refetches /tasks?mode=... A prominent counter shows `alerts_shown` for the current mode so the audience sees the drop (for example 11 alerts to 2).
3. Emergency banner area: tasks in `emergency` are shown at the very top, full width, visually urgent, with the reason.
4. Active cards (WardPulse mode shows at most 2, naive mode shows all): bed, title, one-line reason, how long it has waited, escalated badge, and buttons "Done" and "Not useful" (POST /tasks/{id}/done and /not-useful).
5. Standby queue: compact list below the cards in priority order.
6. Ward overview strip: 20 bed tiles colored by WardStatus, with a stale-data marker and an open-task marker; clicking a bed opens a side panel with PatientDetail (conditions, last readings, a small sparkline per vital drawn with inline SVG or a tiny chart lib, risk tier, reasons).
7. Quick vital-entry: choose a bed, enter hr, sbp, dbp, rr, spo2, temp (optional fields, at least one required, matching VitalsIn), submit to POST /vitals with big buttons; show validation errors.
8. Live updates: connect to GET /stream with EventSource; on tasks_updated refetch /tasks, on ward_updated refetch /ward, sim_tick updates the clock, emergency flashes the banner. In mock mode, simulate updates with a timer so the UI feels alive.
9. Loading, empty and error states everywhere. Keyboard accessible, readable colors (also usable for color-blind users: use labels or icons, not color alone).

Write a short frontend/README.md (install, run: `npm install`, `npm run dev`, env vars). Add basic component tests only if quick; otherwise verify by running the dev server and checking each view.

Done when: `npm run build` succeeds and `npm run dev` shows all sections working in mock mode, including the mode toggle changing the number of alerts.
Finish: update docs/PROGRESS.md (P5 DONE, how to switch from mock to real API), `git status` (never commit node_modules or dist), small commits with prefix `ui:`, push.
```

---

## P6 Integration (after P1 to P5)

```
You are the integration engineer for WardPulse. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md, backend/shared/schemas.py, docs/demo-script.md, docs/PROGRESS.md. P1 to P5 should be DONE; check PROGRESS.md and tell me what is missing before starting.

Your scope: wiring and verification across modules. Fix mismatches with the smallest change, in the module that owns the bug, with one commit per fix and a clear prefix. Do not redesign anything and do not change schemas.py unless a real contract bug is found (then use `contract:` and log it in PROGRESS.md).

Tasks:
1. Start the backend (seed the DB with the real simulator), start the frontend with VITE_USE_MOCK=false, and play through the whole demo from docs/demo-script.md.
2. Write scripts/check_stories.py that drives the running API (using the sim controls and /tasks) and asserts the three stories: (1) Bed 3 has no card and Bed 7 has an active card at the story-1 time; (2) Bed 4 gets repeat_bp and not page_doctor; (3) Bed 12 appears in `emergency` while `active` still holds 2 cards; plus naive mode has clearly more alerts_shown than WardPulse mode at the same moment. Exit non-zero on failure.
3. Fix whatever breaks: field name mismatches, time handling, event delivery, tasks not persisting, aging not progressing across ticks, tasks not clearing, frontend not updating, CORS, etc.
4. Check that a fresh clone works: new venv, install, seed, run backend and frontend from README commands only.
5. Add scripts/run_all.sh and scripts/run_all.ps1 that start backend and frontend together.

Done when: scripts/check_stories.py passes against the real running stack and the demo plays smoothly end to end.
Finish: update docs/PROGRESS.md (P6 DONE, tick the contract tests, list remaining rough edges), `git status`, small commits, push.
```

---

## P7 Evaluation on public data (after P3)

```
You are building the evaluation module for WardPulse so we can show real numbers instead of simulator-only claims. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md (sections 5, 7), backend/shared/schemas.py, docs/safety-rules.md, docs/PROGRESS.md. P3 must be DONE.

Your scope: ONLY backend/evaluation/, backend/tests/test_evaluation.py, and docs/evaluation.md. Never commit raw datasets (data/raw/ is git-ignored).

Tasks:
1. FIRST check dataset access and terms. First choice: the PhysioNet/Computing in Cardiology Challenge 2019 sepsis dataset (hourly ICU records, pipe-separated .psv files per patient, with vitals columns and a SepsisLabel column; verify the exact column names and the label definition from the dataset's own documentation). If you have network access and the terms allow it, download a subset into data/raw/. If you cannot access it, say so clearly, tell me exactly what to download and where to put it, and build everything so it runs the moment the files exist. Also provide a SMALL clearly-labelled SYNTHETIC fallback dataset generator so the pipeline can be demonstrated; any output based on it must say "synthetic" in its dataset name and notes.
2. replay.py: `load_dataset(path, sampling_interval_hours=4.0) -> list[ReplayCase]` mapping dataset columns to our fields (hr, sbp, dbp, rr, spo2, temp; missing stays None), downsampling hourly data to one reading every 4 to 6 hours (seeded jitter) with realistic random gaps, creating a Patient per case (age from the data if present, condition tags empty unless known), and event_time from the dataset's deterioration or sepsis onset label (document exactly how you define it, and note any label caveats in docs/evaluation.md). ReplayCase: patient, readings, event_time or None.
3. metrics.py: `compute_metrics(cases, mode, config) -> SystemMetrics`. Walk each case through time, calling the engine at each new reading (WardPulse via engine.pipeline.evaluate_ward, naive via engine.news2.evaluate_ward_news2). Definitions are in contracts.md section 7: detected = a high-priority card before the event (page_doctor in WardPulse, news2_alert in naive); lead time = event time minus first detection in hours; alerts per nurse-hour; sensitivity; false alert ratio; measurement tasks per nurse-hour (WardPulse only). Be careful to avoid look-ahead (the engine may only see readings up to the current time).
4. run_eval.py: `run() -> EvalResults`, writes backend/evaluation/results.json (for GET /eval/results) and prints a readable table comparing WardPulse and NEWS2. Runnable as `cd backend && python -m evaluation.run_eval`.
5. docs/evaluation.md: dataset, how it was downsampled, definitions, the results table, and honest limitations (ICU data, not ward data; proof of concept; no clinical validation).

Tests: replay downsampling produces gaps of roughly 4 to 6 hours; missing values stay None; no look-ahead; metrics are correct on a tiny hand-made case; run() works on the synthetic fallback.

Done when: `python -m evaluation.run_eval` produces results.json and a table, and `pytest tests/test_evaluation.py` passes.
Finish: update docs/PROGRESS.md (P7 DONE, the headline numbers, whether real or synthetic data was used), `git status`, small commits with prefix `eval:`, push.
```

---

## P8 LightGBM risk model (optional, only after P6 works)

```
You are adding an optional machine-learning input to the WardPulse risk score. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md, backend/shared/schemas.py, docs/evaluation.md, docs/PROGRESS.md. The rules-only engine and evaluation (P3, P6, P7) must already work; if not, stop and say so.

Your scope: ONLY backend/ml/, the small hook in backend/engine/risk.py, and backend/tests/test_ml.py.

Tasks:
1. ml/train.py: build training rows from the replay cases (use the evaluation loader on the public or fallback data) using exactly the same feature definitions as engine/features.py (baseline deviation, trend per hour, shock index, data age, latest values, condition flags). Label: deterioration within the next N hours (choose N and document it). Split BY PATIENT (never by row) to avoid leakage. Train a LightGBM classifier with native missing-value handling, report AUROC and AUPRC on the held-out patients, save the model to ml/saved_model/model.txt (keep it small) and write ml/metrics.json.
2. ml/predict.py: load the model if present and expose `ml_score(features) -> float | None` (None if no model file, so the engine still works without it).
3. engine/risk.py: blend the ML probability into risk_score through the existing `ml_score` hook with a documented weight in EngineConfig-compatible way (do NOT change schemas.py; use a module-level constant if needed and tell me). The rules must remain the safety floor: ML can raise or lower a score only inside the safety limits, never suppress a red-line breach.
4. Re-run the evaluation (python -m evaluation.run_eval) with and without ML and add a short comparison to docs/evaluation.md. If ML does not help, say so honestly and keep it off by default.

Tests: model loads or gracefully returns None; no patient appears in both train and test; the engine still passes all existing tests with the model present and absent.

Done when: all backend tests pass and docs/evaluation.md shows the with/without comparison.
Finish: update docs/PROGRESS.md (P8 DONE or SKIPPED with reason), `git status` (do not commit large files), small commits with prefix `ml:`, push.
```

---

## P9 Polish, demo and presentation prep

```
You are the final polish engineer for WardPulse. Read first, in order: AGENTS.md, docs/PROJECT_CONTEXT.md, docs/contracts.md, docs/demo-script.md, docs/evaluation.md, docs/PROGRESS.md. P6 must be DONE.

Your scope: UX polish in frontend/, docs, and scripts. Do not change engine logic or contracts.

Tasks:
1. Frontend polish: clear visual hierarchy, the mode toggle and alert counter very easy to understand within 5 seconds, smooth transitions, readable on a projector (large text option), the emergency banner unmistakable but not overwhelming, empty states that explain themselves, a small "How to read this screen" help panel.
2. Add a one-click "Demo mode" in the UI that resets the simulation, sets a good speed, and plays the three stories in order, with a small on-screen step caption for each story (for example "Story 1: same breathing rate, different patients").
3. Finalize docs/demo-script.md: exact click-by-click steps, what to say at each step, expected on-screen results, and a fallback if something fails.
4. Finalize README.md: problem, solution, architecture picture (ASCII is fine), results table from docs/evaluation.md, run instructions that work from a FRESH clone (test them), limitations and next steps, and the "decision support, not diagnosis" note.
5. Create docs/presentation-notes.md: a slide-by-slide outline (problem, insight, solution, demo, evaluation, impact, limitations, next steps), the likely judge questions with honest answers (use docs/PROJECT_CONTEXT.md section 6), and the real numbers from the evaluation.
6. Run the full test suite and scripts/check_stories.py and fix anything broken.

Done when: a teammate can clone the repo, follow only the README, and run the full demo.
Finish: update docs/PROGRESS.md (P9 DONE), `git status`, small commits (`ui:` and `docs:`), push.
```
