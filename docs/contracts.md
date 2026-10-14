# WardPulse contracts

This file is the agreement between every module. The code version of the data
shapes is `backend/shared/schemas.py`. If this file and that file ever
disagree, `schemas.py` wins and this file must be fixed in the same commit.

**Read this before changing anything. Do not change anything outside your own module.**

## 1. Hard rules

1. The engine is pure logic. It never touches the web, the database, files or the clock.
2. Time is always passed in as `now`. Never call `datetime.now()` in `engine/`, `simulator/` or `evaluation/`.
3. Every module imports data shapes from `shared.schemas` only. Run everything from the `backend/` directory.
4. Cards come from a closed set (section 4). No LLM, no free-text clinical advice, no drug names, anywhere in the product path.
5. Any vital can be missing (`None`). Missing is information (it affects freshness), never an error.
6. The simulator is seeded and deterministic: same seed, same ward, every time.
7. Hard safety limits are checked before any personal-baseline logic and cannot be overridden by it.
8. No real patient data in the repo, ever. Synthetic or properly public datasets only.
9. WardPulse is decision support, not diagnosis. Keep that note visible in the UI and README.
10. A contract change needs: edit `schemas.py` and this file, tell the team, commit with prefix `contract:`.

## 2. Conventions

| Topic | Rule |
|---|---|
| Datetimes | Timezone-naive, meaning ward/simulation time, ISO 8601 in JSON |
| Units | hr bpm, sbp/dbp mmHg, rr breaths/min, spo2 %, temp degrees C |
| Ids | Integers. `bed` is the bed number 1 to 20 and also identifies the demo patients |
| JSON field names | Exactly as in `schemas.py` (snake_case) |
| Enums | Lowercase string values as in `schemas.py` |
| Commit prefixes | `contract:` `engine:` `sim:` `eval:` `ml:` `api:` `ui:` `docs:` `chore:` |

## 3. Entities (summary)

- **Patient**: id, bed, age, conditions (`copd`, `post_op`, `cardiac`), admitted_at, optional anonymous display_name.
- **VitalsReading**: patient_id, timestamp, hr, sbp, dbp, rr, spo2, temp (each nullable), on_oxygen, consciousness (ACVPU), source (`sim`, `replay`, `manual`).
- **PatientAssessment**: risk_score 0 to 1, risk_tier, crash flag, stale_vitals, hours_since_last_vitals, next_vitals_due, news2_score, reasons (short plain-language lines).
- **Task**: type, target_vital, title, one-line reason, priority, status, emergency flag, escalated flag, created_at, waiting_minutes.
- **TasksResponse**: mode, budget_k, `emergency` list, `active` list (at most K in WardPulse mode), `queue` list, computed `alerts_shown`.
- **WardOverview**: one `WardBed` per bed (status colour, stale flag, has_open_task).
- **WardEvaluation**: what both engines return: assessments + tasks + ward.

## 4. The closed set of cards

| Type | Meaning | Title shown |
|---|---|---|
| `page_doctor` | Escalate | Page the on-duty doctor: Bed N |
| `repeat_bp` | Measure BP again / measure it now | Repeat manual BP: Bed N |
| `repeat_resp_rate` | Recount breathing rate | Recount breathing rate: Bed N |
| `repeat_spo2` | Recheck oxygen level | Recheck oxygen level: Bed N |
| `repeat_heart_rate` | Recheck pulse | Recheck pulse: Bed N |
| `repeat_temp` | Recheck temperature | Recheck temperature: Bed N |
| `full_vitals_recheck` | Everything is old | Take a full set of vitals: Bed N |
| `sit_upright` | Sit patient upright to 45 degrees | as in `schemas.py` |
| `check_oxygen_cannula` | Check cannula position | Check oxygen cannula: Bed N |
| `news2_alert` | Naive comparator only, never in WardPulse mode | Abnormal vitals: Bed N |

Titles are defined once in `TASK_TITLES` in `schemas.py`. A clinician or nursing student should review the wording before the demo.

Every card must carry a one-line `reason` built from real numbers, for example `RR 14 -> 20 over 5h; BP not taken for 7h`.

## 5. Engine contract (`backend/engine/`)

```python
# engine/pipeline.py
def evaluate_ward(
    patients: list[Patient],
    vitals: dict[int, list[VitalsReading]],   # patient_id -> readings, oldest first
    now: datetime,
    config: EngineConfig,
    previous_tasks: list[Task] | None = None, # open tasks from the last evaluation
) -> WardEvaluation: ...

# engine/news2.py  (same signature and return type)
def evaluate_ward_news2(patients, vitals, now, config, previous_tasks=None) -> WardEvaluation: ...
```

Because both return the same shape, the frontend renders either mode with no special cases.

### Expected behaviour

**Features (`features.py`)**
- Personal baseline per vital from readings within `baseline_window_hours`, excluding the latest `baseline_exclude_latest` reading(s), using robust statistics (median and MAD, with a floor on the spread).
- With fewer than `min_baseline_readings`, blend toward a condition-based prior using `prior_blend` (a new admission has no history).
- Trend per hour per vital, shock index (hr / sbp), and age of each vital.

**Safety (`safety.py`)**
- Absolute red lines first. Source for limits: the NEWS2 chart (document it in `docs/safety-rules.md`). A personal baseline may reduce a false alarm only inside safe limits and may never hide an absolute red-line breach.
- `crash = True` for unequivocal crash vitals (for example severe hypotension together with severe tachycardia or very low oxygen). Crash tasks get `emergency = True`.

**Risk (`risk.py`)**
- `risk_score` 0 to 1 from transparent rules, optionally combined with the LightGBM output. Map to `risk_tier` using the cutoffs in `EngineConfig`.

**Freshness**
- Each tier has a due interval (`vitals_due_hours`). A vital is stale when its age exceeds `stale_after_factor` times that interval.
- Stale plus borderline risk produces a measurement task (`repeat_*` or `full_vitals_recheck`), never `page_doctor`.
- Fresh plus high risk produces `page_doctor` and, where relevant, `sit_upright` or `check_oxygen_cannula`.

**Prioritizer (`prioritizer.py`)**
- `priority = risk and urgency component + aging_per_hour x hours waiting`.
- At most `k_budget` tasks have status `active`. The rest are `queued` in priority order.
- Crash tasks bypass the budget and appear in `emergency`.
- A task not completed within `escalation_after_minutes` gets `escalated = True` and a priority boost.
- Task identity: a task is identified by `(patient_id, type)`. While the condition persists, keep the same task id and `created_at` (that is what makes aging work). When the condition clears, drop the task.
- Naive mode (`news2.py`): every patient at or above `news2_alert_threshold` (or with any single parameter scoring 3) becomes a `news2_alert` in `active`, no budget (`budget_k = None`). It uses the standard SpO2 scale 1 for everyone unless `news2_spo2_scale2_for_copd` is set.

## 6. Simulator contract (`backend/simulator/`)

```python
def build_ward(seed: int = 42) -> tuple[list[Patient], list[VitalsReading]]: ...
    # 20 patients plus about 24h of prior history

class Simulator:
    def __init__(self, seed: int = 42): ...
    def advance(self, to: datetime) -> list[VitalsIn]: ...
        # new readings due up to `to`; most beds every 4 to 6h with jitter,
        # some scheduled readings deliberately missed
    def reset(self) -> None: ...
```

The three demo stories use **fixed bed roles**. The numbers are starting points, tune them but keep the roles:

| Story | Beds | Setup | Expected result |
|---|---|---|---|
| 1. Same number, different patients | Bed 3 (COPD), Bed 7 (post-op) | Bed 3 has RR 21 to 23 for the whole 24h. Bed 7 goes RR 14, 14, 15, 17, 22 with pulse rising. Both latest RR = 22. | Bed 3: no card. Bed 7: a card in `active`. |
| 2. Stale BP | Bed 4 | Borderline, falling BP earlier (for example SBP 128 down to 112), last BP 7h old, other vitals 1h old | `repeat_bp` for Bed 4, not `page_doctor` |
| 3. Crash bypass | Bed 12 | At a scripted sim time: SBP about 78, HR about 135, SpO2 about 86. Beds 7 and 4 already fill the K=2 slots. | Bed 12 appears in `emergency` while `active` still holds 2 cards |

Also required for the toggle demo to be convincing:
- At least four more beds with chronic-abnormal but stable vitals (COPD and cardiac) that a fixed-threshold score would flag, so naive mode shows many cards while WardPulse mode shows 2.
- At least three scheduled readings missed across the ward.
- Everything stays reproducible from the seed.

## 7. Evaluation contract (`backend/evaluation/`)

```python
# replay.py
def load_dataset(path: str, sampling_interval_hours: float = 4.0) -> list[ReplayCase]: ...
# ReplayCase: patient: Patient, readings: list[VitalsReading], event_time: datetime | None

# metrics.py
def compute_metrics(cases, mode: Mode, config: EngineConfig) -> SystemMetrics: ...

# run_eval.py
def run() -> EvalResults: ...
```

Definitions (write them in `docs/safety-rules.md` too, judges may ask):
- **Event**: documented deterioration or onset time in the dataset.
- **Detected**: the system raised a high-priority card (`page_doctor` in WardPulse, `news2_alert` in naive mode) before the event.
- **Lead time**: event time minus time of first detection, in hours.
- **Alerts per nurse-hour**: cards raised per simulated hour per 20 beds.
- **Sensitivity** = detected / total events.

Raw datasets go in `data/raw/` and are never committed. Check each dataset's terms of use.

## 8. API contract (`backend/app/api/`)

| Method and path | Request | Response |
|---|---|---|
| `GET /health` | | `{"status": "ok"}` |
| `GET /ward` | | `WardOverview` |
| `GET /patients/{id}` | | `PatientDetail` |
| `GET /tasks?mode=wardpulse` or `news2` | | `TasksResponse` |
| `POST /vitals` | `VitalsIn` | `VitalsReading` (then re-evaluates and emits events) |
| `POST /tasks/{id}/done` | `TaskFeedbackIn` (optional) | `Task` |
| `POST /tasks/{id}/not-useful` | `TaskFeedbackIn` (optional) | `Task` |
| `GET /sim/state` | | `SimState` |
| `POST /sim/control` | `SimControl` | `SimState` |
| `GET /stream` | | Server-sent events of `StreamEvent` |
| `GET /eval/results` | | `EvalResults` |
| `GET /audit?limit=100` | | `list[AuditEntry]` |

Errors use normal HTTP status codes with `{"detail": "..."}` (FastAPI default).

### Stream events

| Event | When | Frontend action |
|---|---|---|
| `tasks_updated` | Task list changed | Refetch `GET /tasks` |
| `ward_updated` | Any bed changed | Refetch `GET /ward` |
| `sim_tick` | Each clock tick, `data` = `SimState` | Update clock |
| `emergency` | A crash bypass card appeared | Flash the emergency banner |

## 9. Database tables (`backend/app/db/`)

Only `app/` touches the database. SQLite.

| Table | Columns |
|---|---|
| `patients` | id, bed, age, conditions (JSON list), admitted_at, display_name |
| `vitals` | id, patient_id, timestamp, hr, sbp, dbp, rr, spo2, temp, on_oxygen, consciousness, source |
| `tasks` | id, patient_id, bed, type, target_vital, title, reason, priority, status, emergency, escalated, created_at, resolved_at |
| `audit_log` | id, timestamp, event_type, patient_id, task_id, details (JSON) |
| `feedback` | id, task_id, kind (`done` or `not_useful`), note, timestamp |

The database file is created by `python -m app.db.seed` and is never committed.

## 10. Contract tests (must exist in `backend/tests/`)

1. Story 1: Bed 3 at RR 22 yields no card; Bed 7 at RR 22 yields an active card.
2. Story 2: Bed 4 with stale BP yields `repeat_bp`, not `page_doctor`.
3. Story 3: with 2 active cards, a crash on Bed 12 appears in `emergency` and `active` still has 2.
4. Budget: with 10 abnormal patients, `len(active) <= k_budget` in WardPulse mode.
5. Naive mode on the same data shows more `alerts_shown` than WardPulse mode.
6. Aging: a queued task's priority increases with waiting time.
7. Escalation: an ignored active task becomes `escalated` after `escalation_after_minutes`.
8. Missing data: a patient with all vitals `None` does not crash the engine.
9. Determinism: same seed gives the identical ward and results.
10. Safety: a personal baseline never suppresses an absolute red-line breach.
