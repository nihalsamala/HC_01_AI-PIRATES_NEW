# WardPulse: project context and handoff

Read this file fully before doing anything. It is the shared memory of the project.
If you are a new agent or a new chat session, this file plus `docs/PROGRESS.md`
plus `docs/contracts.md` is everything you need to continue.

Stable facts live here. What is done and what is next lives in `docs/PROGRESS.md`.
Exact data shapes live in `backend/shared/schemas.py` (source of truth).

---

## 1. Snapshot

- **Event:** hackathon (form page says VJ Hackathon 2K26). Domain: **Healthcare**.
- **Problem statement:** Healthcare PS1, *AI Early Warning System for Patient Health Deterioration*. Monitor patient vitals and predict deterioration (sepsis, shock, respiratory failure) hours before the patient crashes.
- **Stage:** Round 1 (abstract, objective and goals form, and the spoken presentation of objective and goals) is done. **Round 2 is now:** build a working prototype, present it to a jury, and commit every single change into the repo the organizers provided (no required structure, README was empty).
- **Time:** roughly 24 hours remained when this file was first written (14 Oct 2026). Work fast, keep a working demo at all times.
- **Team:** 4 members who build mostly with AI coding agents in Antigravity by pasting prompts from `docs/AGENT_PROMPTS.md`. Nominal roles: (1) simulation and data, (2) machine learning, (3) backend and prioritization engine, (4) frontend. Any member can run any work package.
- **The user is not from a healthcare background.** Explain medical terms in plain words. Be honest and direct, including about weaknesses.

## 2. The problem in plain words

Glossary:
- **Vitals:** heart rate, blood pressure (BP, systolic = sbp, diastolic = dbp), oxygen level (SpO2), respiratory rate (RR, breaths per minute), temperature.
- **Deterioration:** a patient who looks stable getting seriously worse.
- **Sepsis:** the body overreacting to infection; treatable if caught early, often fatal if late.
- **General ward vs ICU:** ICU has continuous machines; a general ward has a nurse measuring vitals by hand every few hours.
- **COPD:** chronic lung disease; COPD patients normally breathe faster and have lower oxygen.
- **Post-op:** recovering from surgery.
- **Alarm fatigue:** staff stop reacting because alarms fire too often.
- **NEWS2:** the standard hospital early-warning score (National Early Warning Score 2). We use it as the honest comparator.

The catch in the problem statement: it quietly assumes an ICU with continuous sensors. In Indian district hospitals and general wards, one nurse often covers 20 to 30 patients, vitals are manual every 4 to 6 hours (sparse, with gaps), and noisy alerts get ignored.

**The real problem we solve:** with sparse, patchy vitals and an overloaded nurse, *what should she do in the next 15 minutes?*

## 3. The idea: WardPulse (a "Nurse Attention Allocator")

Not a risk score. An AI priority inbox that tells the nurse the top actions.

Three pillars:
1. **Personal baseline:** judge each patient against their own recent history, not only global limits. A COPD patient at RR 22 may be normal; a post-op patient rising 14 to 22 is not.
2. **Risk and freshness are separate:** fresh vitals plus high risk gives "page the doctor". Borderline vitals plus an old reading (for example BP 7 hours old) gives "measure BP now", never "patient is dying".
3. **Attention budget K=2 plus Crash Bypass:** the nurse sees at most 2 active cards; the rest wait in a queue. Unequivocal crash vitals bypass the budget and show an emergency banner. Cards come from a **closed set** of safe nursing actions (no LLM, no drugs).

Added after critical review (these are decisions, keep them):
- Comparator for the "Naive AI" toggle is **real NEWS2**, not a strawman.
- Validate on a **public dataset** downsampled to ward-like gaps, to avoid circular evaluation on our own simulator. Report **lead time** (hours of warning).
- Personal baselines are weak with 4 to 6 readings, so: lagged baseline (exclude latest reading), robust statistics, blend with a **condition-based prior** when history is thin, and a **cold-start** rule for new admissions.
- **Hard safety limits** (from the NEWS2 chart) are checked first and can never be overridden by a personal baseline.
- K=2 failure modes handled: **aging** (waiting tasks gain priority), **escalation** (ignored cards escalate), a quiet **whole-ward overview strip** so the nurse is not blind, K configurable.
- Extras: one-line **reason** on every card, risk-based re-measure schedule, trend features and shock index (hr / sbp), **simulation clock** (play, pause, speed), "not useful" feedback button, audit log, visible "decision support, not diagnosis" note.
- LightGBM is **optional**, one input to a transparent scoring layer (it handles missing values natively). The rules version must work end to end first.

## 4. Architecture

```
Sources:  simulator | dataset replay | nurse vital entry
              |
        Patient and vitals store (SQLite)
              |
   WardPulse engine (pure logic):
     features -> safety + risk -> task cards -> prioritizer (K, aging, bypass)
              |
        FastAPI service (+ server-sent events)
              |
   Nurse console (React)  |  Demo controls (mode toggle, sim clock)

Separate pipeline: replay data -> [WardPulse engine, NEWS2 baseline] -> metrics
```

Key design rule: **the engine knows nothing about the web, the database, files or the clock.** It takes patients, readings and `now`, and returns a `WardEvaluation`. The same engine runs live, in the simulator and in evaluation.

Stack (assumed, no organizer constraint was found): Python, FastAPI, SQLite (SQLAlchemy), Pydantic v2, LightGBM, pytest; frontend React + Vite + TypeScript + Tailwind.

Repo layout:

```
AGENTS.md
README.md
.gitignore
docs/        PROJECT_CONTEXT.md, PROGRESS.md, AGENT_PROMPTS.md, contracts.md, safety-rules.md, demo-script.md
backend/
  requirements.txt
  shared/    schemas.py        <- contracts in code
  app/       main.py, api/, db/
  engine/    config.py, features.py, safety.py, risk.py, freshness.py, tasks.py, prioritizer.py, pipeline.py, news2.py
  simulator/ ward.py, scenarios.py, clock.py
  evaluation/ replay.py, metrics.py, run_eval.py
  ml/        train.py, saved_model/
  tests/
frontend/    src/
data/        sample/, raw/ (raw never committed)
scripts/
```

Always run Python from the `backend/` directory (`from shared.schemas import ...`).

## 5. Rules everyone follows

The full list is in `docs/contracts.md` section 1. The ones that matter most:
1. Engine is pure; time is passed in as `now`; no `datetime.now()` in engine, simulator or evaluation.
2. Import data shapes only from `shared.schemas`. Do not edit `schemas.py` or `contracts.md` except through a deliberate contract change (commit prefix `contract:`, announce in `docs/PROGRESS.md`).
3. Closed set of cards. No LLM output or drug advice in the product path.
4. Any vital may be `None`. Missing is information, never an error.
5. Simulator is seeded and deterministic.
6. Hard safety limits first; personal baselines never hide a red-line breach.
7. No real patient data in the repo.
8. Work only inside your own folder.

## 6. Demo plan (what the jury sees)

A nurse console on a simulated 20-bed ward:
- Emergency banner area, 2 active task cards with one-line reasons, a standby queue, a 20-bed overview strip, vital-entry form, simulation clock controls.
- **Toggle: Naive AI (NEWS2) vs WardPulse.** Same data; naive mode shows many cards, WardPulse shows 2. The counter `alerts_shown` makes this visible.

Three scripted stories (fixed bed roles, details in `docs/contracts.md` section 6):
1. **Bed 3 (COPD) vs Bed 7 (post-op)** both at RR 22: Bed 3 calm, Bed 7 gets a card.
2. **Bed 4 stale BP:** a "Repeat manual BP" task, not "page doctor".
3. **Bed 12 crash:** appears in the emergency area even though 2 cards already fill the budget.

Likely judge questions and honest answers:
- *"What if a third patient crashes?"* Crash bypass shows emergencies above the budget.
- *"Isn't your simulator circular?"* Yes for the demo; accuracy claims come from a public dataset downsampled to ward-like gaps, and we say it is a proof of concept.
- *"Why not just NEWS2?"* NEWS2 uses the same limits for everyone and has no notion of stale data or nurse workload; we compare against it directly on lead time and alerts per nurse-hour.
- *"Is it clinically validated?"* No. It is decision support with a validation roadmap.

## 7. Evaluation plan

- Replay a public dataset (PhysioNet 2019 sepsis challenge is the first choice; check access and terms first), downsample to one reading every 4 to 6 hours with realistic gaps.
- Run WardPulse and NEWS2 over the same patients. Metrics: sensitivity, median lead time (hours), alerts per nurse-hour, false alert ratio, measurement tasks per nurse-hour.
- If the dataset is not accessible in time, run a clearly labelled synthetic evaluation and say so. Never present synthetic results as clinical performance.

## 8. Round 1 submission text (already decided)

Google form answers are limited to **200 characters**:
- Objective: *Nurses in understaffed wards check vitals every 4-6 hours and miss early deterioration. WardPulse tells the nurse the top 2 actions for the next 15 minutes, based on each patient's own baseline.*
- Goals: *Warn hours before a crash from sparse vitals, cut alerts to 2 tasks at a time, turn outdated readings into 'measure now' tasks, and prove it against NEWS2 on a simulated ward and public data.*

Longer versions (about 200 words each) exist for the presentation: five goals (warn earlier, cut alert overload, fair to every patient via baselines, turn missing data into action, stay safe and trustworthy) and expected outcomes (working prototype, side-by-side demo, tested on public data, no new hardware, scalable to district hospitals).

## 9. Honest caveats (do not overclaim)

- Do not say "nobody has done this". Say existing tools assume ICU-style data and optimize accuracy; we optimize nurse attention under real ward constraints.
- Do not claim clinical accuracy. Claim logic validated on public data, designed for clinical validation next.
- Do not quote death or staffing statistics unless a source is cited.
- `schemas.py` was written without being executed (no Pydantic available at the time). The first agent task verifies it.
- Default numbers in `EngineConfig` are placeholders; card wording and safety limits should be reviewed by a clinician or nursing student before the demo.
- NEWS2 SpO2 Scale 2 is for clinician-confirmed hypercapnic patients; using the COPD tag as a proxy is a simplification. Default for the naive comparator is Scale 1 for everyone.
- Dataset access (PhysioNet / MIMIC) was not verified.

## 10. Working agreements

- One small logical change per commit. Prefixes: `contract:` `engine:` `sim:` `eval:` `ml:` `api:` `ui:` `docs:` `chore:`.
- Run `git status` and `git diff` before every commit; AI agents leave stray files. Pull before push. Never force-push.
- After every task, update `docs/PROGRESS.md` (status, what changed, anything the next agent must know) and commit it.
- Never commit: `.env`, `venv/`, `node_modules/`, `*.db`, `data/raw/`, build output, logs.
- Keep a working demo at all times. If a task is blocked, write the blocker in `docs/PROGRESS.md` and move on to the next package.

## 11. Work packages

P0 bootstrap, P1 simulator, P2 engine A (features, safety, risk, NEWS2), P3 engine B (freshness, tasks, prioritizer, pipeline), P4 backend API and DB, P5 frontend, P6 integration, P7 evaluation, P8 LightGBM (optional), P9 polish and demo.
Full prompts: `docs/AGENT_PROMPTS.md`. Status: `docs/PROGRESS.md`.

Suggested 24-hour order: P0 first (about 1h). Then P1, P2, P4 and P5 in parallel (P5 builds against mock data). Then P3, P6. Then P7. P8 only if time remains. Reserve the last 4 hours for P9, the presentation and rehearsal.

## 12. How an assistant (Claude) should help the user

The human has very limited assistant usage left, so the build is done by Antigravity agents that update this repo themselves. If you are a new Claude chat taking over:
1. Read `docs/PROGRESS.md` first (table, contract tests, Change log, Next recommended prompt), then this file, then `docs/contracts.md`.
2. Tell the human in 3 lines where the project stands and what is risky.
3. Give the next prompt as a SHORT launcher line (see `docs/CLAUDE_TAKEOVER.md`) that points the agent at the right block in `docs/AGENT_PROMPTS.md`. Only write a new full prompt if a package needs to change or a bug needs a targeted fix.
4. If an agent reports a failure, ask for its final message and the failing test output, then give a targeted fix prompt.
5. Keep explanations in simple words, define any healthcare term, be honest about weaknesses, and give text-to-paste in code blocks.
6. Never edit `schemas.py` or `contracts.md` without a deliberate `contract:` decision logged in PROGRESS.md.
