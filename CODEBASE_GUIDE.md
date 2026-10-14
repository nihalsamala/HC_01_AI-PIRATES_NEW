# WardPulse Codebase Guide & Complete Directory Reference

WardPulse (`HC_01_AI-PIRATES`) is an AI-assisted early warning and nurse attention allocation system designed for understaffed hospital wards. Rather than overwhelming clinical staff with unconstrained threshold alarms, WardPulse bounds nurse cognitive load by calculating patient-specific baselines and presenting at most **K cards** (default 2) for immediate action within a 15-minute operational window.

---

## 1. High-Level Repository Structure

```text
HC_01_AI-PIRATES/
├── AGENTS.md                  # Strict instructions, constraints, and handoff protocols for AI agents
├── CODEBASE_GUIDE.md          # Comprehensive architectural and file-by-file reference guide (this file)
├── README.md                  # Project overview, quickstart instructions, system architecture, and evaluation
├── .gitignore                 # Excludes environments, compiled artifacts, caches, and database files
├── backend/                   # Python FastAPI service, clinical algorithmic engine, simulator, ML, and tests
│   ├── requirements.txt       # Python dependencies (FastAPI, SQLAlchemy, Pydantic, LightGBM, pytest, etc.)
│   ├── wardpulse.db           # SQLite database (persisted state of patients, readings, tasks, and audit logs)
│   ├── app/                   # FastAPI web layer, endpoints, SSE streams, database schemas, and background loops
│   │   ├── main.py            # Application entrypoint with CORS configuration and startup lifespan
│   │   ├── services.py        # Central orchestrator: re-evaluation service, SSE event bus, and sim clock worker
│   │   ├── api/               # API routing definitions
│   │   │   └── routes.py      # All REST endpoints matching contracts.md
│   │   └── db/                # Persistence layer
│   │       ├── models.py      # SQLAlchemy ORM models for patients, vitals, tasks, audit log, and feedback
│   │       ├── seed.py        # Database seed script populating 20 simulated beds from the ward simulator
│   │       └── session.py     # SQLite connection engine, session factory, and dependency injection helpers
│   ├── engine/                # Pure logic clinical decision engine (no I/O, no DB, time passed as parameter)
│   │   ├── config.py          # Default engine parameters (K-budget, thresholds, windows, weights)
│   │   ├── features.py        # Personal baseline calculator (MAD/median), condition priors, and drift features
│   │   ├── freshness.py       # Tier-based vitals cadence scheduler and data staleness detector
│   │   ├── news2.py           # Standard Royal College of Physicians NEWS2 benchmark comparator (Naïve AI)
│   │   ├── pipeline.py        # Core evaluation pipeline executing the full WardPulse assessment cycle
│   │   ├── prioritizer.py     # Attention allocator: aging factor, escalation, K-budgeting, and crash bypass
│   │   ├── risk.py            # Transparent composite risk scoring combining rules, priors, and safety floors
│   │   ├── safety.py          # Red-line safety limits and unequivocal crash physiological collapse detector
│   │   └── tasks.py           # Closed-set action card generator (no LLM hallucination, no arbitrary drug advice)
│   ├── evaluation/            # Rigorous comparative benchmark framework (WardPulse vs Naïve NEWS2)
│   │   ├── metrics.py         # Evaluation metrics: sensitivity, lead time, alert rate, and measurement burden
│   │   ├── replay.py          # Zero-lookahead historical vitals replay loader with realistic missingness
│   │   ├── results.json       # Benchmark evaluation output metrics comparing WardPulse against NEWS2
│   │   └── run_eval.py        # Evaluation runner CLI outputting side-by-side performance comparisons
│   ├── ml/                    # Machine learning deterioration risk model (LightGBM tabular classifier)
│   │   ├── features.py        # Tabular feature extraction converting clinical features to model vectors
│   │   ├── metrics.json       # Cross-validated offline training evaluation metrics (AUROC, AUPRC)
│   │   ├── predict.py         # Production inference wrapper with graceful fallback to pure rules
│   │   ├── train.py           # Model training pipeline using patient-level stratified train/test split
│   │   └── saved_model/
│   │       └── model.txt      # Serialized LightGBM binary tree model artifact
│   ├── shared/                # Universal single source of truth contracts
│   │   └── schemas.py         # Pydantic schemas, enums, task codes, and data models shared across modules
│   ├── simulator/             # Deterministic 20-bed hospital ward simulation engine
│   │   ├── clock.py           # Controllable virtual simulation clock (play, pause, speed, step)
│   │   ├── scenarios.py       # Scripted clinical stories (Story 1: drift, Story 2: stale BP, Story 3: crash)
│   │   └── ward.py            # Generator producing 20 realistic medical/surgical patients with 24h histories
│   └── tests/                 # Automated pytest test suite
│       ├── fixtures.py        # Handcrafted clinical patient and reading fixtures
│       ├── test_api.py        # Tests for all 12 REST API endpoints, CORS, database persistence, and SSE
│       ├── test_engine_a.py   # Tests for NEWS2 calculation, features, personal baselines, and safety checks
│       ├── test_engine_b.py   # Tests for freshness, candidate tasks, prioritizer, K-budget, and aging
│       ├── test_evaluation.py # Tests for replay generator, missing data handling, and metric calculation
│       ├── test_ml.py         # Tests for ML feature vector extraction, training pipeline, and inference
│       ├── test_schemas_smoke.py # Contract validation tests asserting schema constraints
│       └── test_simulator.py  # Tests for simulation clock, patient generator, and clinical scenarios
├── data/                      # Clinical datasets and training corpora
│   ├── raw/                   # Destination folder for raw external datasets (e.g., PhysioNet CinC 2019 .psv)
│   └── sample/                # Sample test data extracts for local debugging
├── docs/                      # Architectural specifications, medical guidelines, and demo documentation
│   ├── AGENT_PROMPTS.md       # Incremental task definitions across development lanes (P0 to P9)
│   ├── CLAUDE_TAKEOVER.md     # Context handoff notes and operational guidelines for agent continuation
│   ├── P0_COMPLETION_REPORT.md# Foundation milestone audit verifying skeletons, dependencies, and smoke tests
│   ├── PROGRESS.md            # Active project log: table of work packages, contract tests, and open questions
│   ├── PROJECT_CONTEXT.md     # Foundational requirements, problem statement, design decisions, and core rules
│   ├── contracts.md           # API specification, route definitions, schemas, and contract acceptance criteria
│   ├── demo-script.md         # Verbatim hackathon demonstration presentation script and clinical walk-through
│   ├── evaluation.md          # Scientific evaluation methodology, dataset description, and comparative results
│   ├── presentation-notes.md  # Slide outline, competitive differentiator breakdown, and judge Q&A defense
│   └── safety-rules.md        # Medical safety guidelines, physiological red-lines, and protocol definitions
├── frontend/                  # React + TypeScript + Vite + Tailwind CSS nurse station web console
│   ├── .env                   # Frontend environment configuration (VITE_USE_MOCK, VITE_API_URL)
│   ├── index.html             # HTML single page application host template
│   ├── package.json           # Frontend dependencies (React 19, Lucide icons, Tailwind CSS 4, Vite 8)
│   ├── vite.config.ts         # Vite build tool and development server configuration
│   └── src/                   # React source code
│       ├── App.tsx            # Main layout assembling Left Nav, TopBar, AttentionCards, RightSidebar, Scrubber
│       ├── index.css          # Design tokens, accessibility modes, pulse animations, and projector classes
│       ├── main.tsx           # React DOM root bootstrapping App
│       ├── types.ts           # TypeScript interfaces matching backend/shared/schemas.py contracts
│       ├── api/
│       │   └── client.ts      # HTTP client for backend REST API, SSE stream listener, and mock store fallback
│       ├── components/        # Visual user interface components
│       │   ├── ActiveCards.tsx       # Original active cards list component
│       │   ├── AttentionCards.tsx    # Restyled 2-column cards layout with vitals trends and DO NOW checklist
│       │   ├── DemoBanner.tsx        # Guided demo story step-through banner
│       │   ├── EmergencyBanner.tsx   # Critical crash bypass alert banner spanning top of screen
│       │   ├── Header.tsx            # Navigation header component
│       │   ├── HelpModal.tsx         # Clinical rationale and reference modal
│       │   ├── ModeToggle.tsx        # Naïve AI vs WardPulse mode toggle pill with noise comparison
│       │   ├── NavSidebar.tsx        # Left narrow rail: Console, Ward map, Handover, Protocols, Proof, How it thinks
│       │   ├── PatientDetailPanel.tsx# Slide-over drawer with patient history and vital sparkline graphs
│       │   ├── Placeholders.tsx      # Clean placeholder views for secondary navigation tabs
│       │   ├── QuickVitalsModal.tsx  # Fast bedside vital sign entry form for any bed
│       │   ├── ReplayTimeline.tsx    # Bottom scrubber bar with time ticks and interactive story chips
│       │   ├── RightSidebar.tsx      # Enter vitals, I'm worried, 20-bed Ward at a glance grid, Live Proof table
│       │   ├── Sparkline.tsx         # Lightweight inline SVG vital sign trend graph
│       │   ├── StandbyQueue.tsx      # Ranked list of pending cards waiting in reserve
│       │   ├── TopBar.tsx            # Top header bar: logo, toggle, sim clock, speed selector, K selector, profile
│       │   ├── WardStrip.tsx         # Compact 20-bed overview strip
│       │   └── WorriedModal.tsx      # "I'm worried" bedside nurse escalation concern dialog
│       └── mock/
│           └── mockData.ts    # Rich offline mock dataset for all 20 beds and 3 clinical deterioration stories
└── scripts/                   # Cross-platform orchestration scripts
    ├── check_stories.py       # End-to-end integration test driving simulation and asserting the 3 clinical stories
    ├── run_all.ps1            # Windows PowerShell one-click launcher starting backend and frontend together
    ├── run_all.sh             # Linux/macOS Bash one-click launcher starting backend and frontend together
    ├── run_backend.ps1        # Standalone Windows PowerShell script to start the FastAPI server
    └── run_backend.sh         # Standalone Linux/macOS Bash script to start the FastAPI server
```

---

## 2. Detailed Folder & File Breakdown

### Root Directory

- **`AGENTS.md`**: Strict instructions and governance rules for AI coding agents operating on the WardPulse repository. Defines modular isolation rules, schema immutability, pure logic engine constraints, and post-task verification checklists.
- **`README.md`**: Primary documentation for developers, judges, and users. Contains the project mission, clinical problem statement, step-by-step setup guides, architecture diagrams, benchmark results table, and hackathon presentation tips.
- **`CODEBASE_GUIDE.md`**: This file. Complete architectural breakdown and file-by-file directory reference.
- **`.gitignore`**: Excludes transient files, virtual environments (`backend/.venv/`), node dependencies (`frontend/node_modules/`), compiled bundles (`dist/`), temporary cache directories (`__pycache__/`, `.pytest_cache/`), and SQLite database files (`*.db`).

---

### `backend/`

The backend provides the API, database persistence, automated evaluation, simulator, and machine learning components. It runs under Python 3.10+ (tested with Python 3.14).

- **`requirements.txt`**: Declares Python package dependencies:
  - `fastapi`, `uvicorn[standard]`, `sse-starlette` (web framework, server, server-sent events)
  - `pydantic` (strict typed contracts and runtime validation)
  - `sqlalchemy` (relational database ORM)
  - `lightgbm`, `scikit-learn`, `numpy` (optional ML classifier and feature tooling)
  - `pytest`, `pytest-asyncio`, `httpx` (automated test framework)
- **`wardpulse.db`**: Local SQLite database storing patients, vitals readings, task state history, and clinical audit events. Created automatically via `backend/app/db/seed.py`.

#### `backend/app/` (FastAPI Application Layer)
Connects the clinical decision engine with HTTP endpoints, background event streams, and database persistence.

- **`main.py`**: Initializes the FastAPI application instance. Configures permissive Cross-Origin Resource Sharing (CORS) for development ports (`5173`, `5174`, `3000`), sets up the lifespan context manager to initialize database tables on startup, mounts all API routes, and exposes a `/health` endpoint.
- **`services.py`**: The application orchestration backbone.
  - Implements `run_evaluation_and_emit(sim_time)` to run the pure logic engine against current database state and push results to connected clients.
  - Houses the asynchronous `SimClock` class managing play/pause state, time progression, and speed multiplier loops.
  - Provides the `EventBus` managing Server-Sent Events (SSE) queues.
  - Implements conversion helpers between SQLAlchemy database rows and Pydantic schema contracts.

#### `backend/app/api/`
- **`routes.py`**: Implements all 12 REST API endpoints defined in `contracts.md`:
  - `GET /ward`: Retrieves current status of all 20 beds (`WardOverview`).
  - `GET /patients/{id}`: Detailed patient profile with recent vitals and open tasks.
  - `GET /tasks?mode={wardpulse|news2}`: Active cards, standby queue, and emergency tasks.
  - `POST /vitals`: Ingests new bedside measurements and triggers immediate re-evaluation.
  - `POST /tasks/{id}/done`: Marks a card as completed by the nurse.
  - `POST /tasks/{id}/not-useful`: Dismisses a card with optional feedback notes for auditing.
  - `GET /sim/state` & `POST /sim/control`: Reads and modifies simulation clock state.
  - `GET /stream`: Server-Sent Events (SSE) stream broadcasting real-time updates.
  - `GET /eval/results`: Reads pre-computed comparative benchmark statistics from `evaluation/results.json`.
  - `GET /audit`: Returns chronological clinical audit trail records.

#### `backend/app/db/`
- **`models.py`**: SQLAlchemy 2 declarative database models:
  - `PatientRow`: Patient identifier, bed number, age, admission timestamp, conditions.
  - `VitalsRow`: Timestamped vital sign measurements with provenance (`sim`, `manual`, `replay`).
  - `TaskRow`: Persisted engine task cards, priority score, status, and resolution timestamps.
  - `AuditLogRow`: Immutable clinical audit trail recording every state change and user action.
  - `FeedbackRow`: Feedback comments captured when nurses flag cards as "not useful".
- **`session.py`**: Database setup creating the SQLite engine (`wardpulse.db`), configuring foreign key pragmas, defining `SessionLocal`, and exposing the FastAPI `get_db` dependency.
- **`seed.py`**: CLI seed utility (`python -m app.db.seed`) that clears existing database tables and populates a 20-bed ward populated with 24 hours of simulated physiological vitals.

---

### `backend/engine/` (Clinical Decision Engine)

A **pure logic** engine with zero network, filesystem, or clock access. Deterministic time is always passed in as `now: datetime`.

- **`config.py`**: Instantiates `DEFAULT_CONFIG` with default clinical constants (K-budget = 2, freshness intervals, escalation windows, safety thresholds).
- **`features.py`**: Extracts personalized physiological baselines:
  - Uses robust Median Absolute Deviation (MAD) over a rolling 24-hour window (excluding the latest reading to avoid baseline contamination by acute deterioration).
  - Blends empirical patient baseline with condition-specific population priors (e.g., higher baseline respiration for COPD, lower baseline BP for post-op).
  - Computes physiological drift indicators (rate of change, trajectory direction).
- **`freshness.py`**: Monitors vital sign cadence. Assigns maximum due intervals per risk tier (Low: 6h, Medium: 4h, High: 2h, Critical: 1h), detects stale vitals, and flags borderline-and-stale cases.
- **`news2.py`**: Faithful implementation of the UK Royal College of Physicians National Early Warning Score (NEWS2). Serves as the baseline "Naïve AI" comparator to demonstrate noise reduction.
- **`pipeline.py`**: Core entrypoint `evaluate_ward(patients, vitals, now, config, previous_tasks)`. Evaluates every patient, checks red lines, computes risk, generates candidate cards, prioritizes, and outputs a complete `WardEvaluation`.
- **`prioritizer.py`**: Allocates nurse attention. Limits active cards to at most `k_budget`, applies chronological aging bonuses so neglected tasks rise in priority, escalates cards ignored past 30 minutes, and implements the **Crash Bypass** (critical patients jump straight to emergency banner without consuming the K-budget).
- **`risk.py`**: Computes transparent, explainable 0–1 risk scores and assigns risk tiers (`low`, `medium`, `high`, `critical`). Blends rule-based clinical logic with condition priors, incorporates optional ML probability when enabled, and strictly enforces red-line floor overrides.
- **`safety.py`**: Clinical safety boundaries.
  - `is_crash(reading)`: Detects unequivocal physiological collapse (severe shock SBP < 80, critical hypoxia SpO2 < 88%, severe brady/tachycardia).
  - `check_red_lines(reading, patient, config)`: Detects parameter breaches that can never be suppressed by personalized baselines.
- **`tasks.py`**: Produces actionable cards exclusively from a **closed set** of pre-authorized clinical protocols (e.g. `sit_upright`, `check_oxygen_cannula`, `repeat_bp`, `page_doctor`). Guarantees no generative LLM hallucination and no dangerous unauthorized medication advice.

---

### `backend/evaluation/` (Comparative Evaluation Framework)

Empirically benchmarks WardPulse against the traditional NEWS2 threshold standard on 50 simulated general ward deterioration profiles.

- **`replay.py`**: Simulates realistic ward monitoring by downsampling continuous data to 4–6 hour monitoring intervals with random jitter and intentional missing vitals. Operates under strict **zero-lookahead** guarantees.
- **`metrics.py`**: Mathematical metrics calculator: sensitivity, median early warning lead time, alert rate per nurse-hour, and triage measurement task burden.
- **`run_eval.py`**: Command-line evaluation executable (`python -m evaluation.run_eval`) that processes the cohort through both systems and generates side-by-side metric tables.
- **`results.json`**: Cached machine-readable output of the evaluation run (WardPulse: 87.5% sensitivity, 2.0h lead time, 1.15 alerts/nurse-hr vs NEWS2: 1.17 alerts/nurse-hr with high false alarm ratio).

---

### `backend/ml/` (LightGBM Risk Model)

Optional machine learning deterioration classifier supporting the hybrid clinical decision framework.

- **`features.py`**: Extracts 14-dimensional tabular feature vectors from raw clinical vitals and personal baseline drifts with native NaN missing-value representation.
- **`train.py`**: Trains a gradient-boosted decision tree (`lightgbm.LGBMClassifier`) using patient-level stratified cross-validation to prevent temporal data leakage.
- **`predict.py`**: Inference module providing `predict_risk(features)`. Gracefully returns `None` if the model artifact is absent or disabled.
- **`metrics.json`**: Offline validation metrics demonstrating AUROC and AUPRC performance.
- **`saved_model/model.txt`**: Serialized 51 KB LightGBM binary tree model.

---

### `backend/shared/` (Single Source of Truth)

- **`schemas.py`**: Central Pydantic contract definition file imported by all backend modules and mirrored by the frontend. Defines all Enums (`TaskType`, `RiskTier`, `WardStatus`, `Mode`, `VitalName`), data shapes (`Patient`, `VitalsReading`, `Task`, `TasksResponse`, `WardOverview`, `PatientDetail`, `EvalResults`), and clinical card action titles.

---

### `backend/simulator/` (Ward Simulation Engine)

- **`clock.py`**: Virtual deterministic simulation clock supporting play, pause, speed stepping, and synchronized time broadcasts.
- **`ward.py`**: Generates a 20-bed hospital ward with diverse medical, post-operative, and COPD patients, complete with 24 hours of pre-admission and inpatient vital histories.
- **`scenarios.py`**: Implements the 3 canonical clinical demonstration stories:
  - **Story 1 (07:00)**: Bed 3 (COPD) has RR 22 (normal for them, calm) vs Bed 7 (Post-op) has RR 22 (abnormal drift vs base 14, active card raised).
  - **Story 2 (09:00)**: Bed 4 has stale BP (7 hours old). Triggers `repeat_bp` triage card rather than a premature false-alarm doctor page.
  - **Story 3 (11:00)**: Bed 12 suffers sudden septic shock (SBP 78, HR 135). Crash bypass immediately fires full-width emergency alert while active budget preserves top 2 bedside tasks.

---

### `backend/tests/` (Automated Test Suite)

- **`fixtures.py`**: Shared test fixtures: mock patients with COPD and post-op conditions, baseline vitals series, and 10-abnormal patient stress wards.
- **`test_api.py`**: Validates all 12 FastAPI endpoints, CORS headers, SSE broadcasts, and database CRUD.
- **`test_engine_a.py`**: Validates personal baselines, MAD calculation, NEWS2 scoring, and red-line safety checks.
- **`test_engine_b.py`**: Validates data freshness rules, card generation, priority aging, and K-budget enforcement.
- **`test_evaluation.py`**: Validates replay downsampling, zero-lookahead integrity, and metric computations.
- **`test_ml.py`**: Validates ML feature extraction, model inference, and rule-based safety overrides.
- **`test_schemas_smoke.py`**: Verifies schema validation boundaries, vital ranges, and Pydantic constraints.
- **`test_simulator.py`**: Verifies deterministic ward generation, scenario event triggers, and clock operations.

---

### `data/`

- **`raw/.gitkeep`**: Staging directory for external clinical datasets (e.g. PhysioNet Challenge 2019 sepsis cohort).
- **`sample/.gitkeep`**: Staging directory for local test extracts and debug cases.

---

### `docs/`

- **`PROJECT_CONTEXT.md`**: Core hackathon charter: explains *why* WardPulse exists, why attention allocation matters over raw alarms, and documents foundational architectural decisions.
- **`contracts.md`**: Technical specification of all data models, API endpoints, error responses, and the 10 formal contract acceptance tests.
- **`PROGRESS.md`**: Active development tracker listing the status of all packages (P0 through P9), contract test results, open architectural questions, and chronological change logs.
- **`safety-rules.md`**: Clinical safety documentation defining physiological red-lines, crash criteria, and the closed-set protocol definitions.
- **`evaluation.md`**: Comprehensive scientific benchmark writeup reporting sensitivity, lead time, and noise reduction across 50 patient cases.
- **`demo-script.md`**: Script for presentations, including exact spoken lines, timing, and click-by-click instructions for judges.
- **`presentation-notes.md`**: Slide deck outline, competitive differentiation matrix, and answers to common judge questions.
- **`AGENT_PROMPTS.md`**: Prompts defining the 10 work packages (P0 to P9) used during development.
- **`CLAUDE_TAKEOVER.md`**: Operational guide for new AI conversations taking over development.
- **`P0_COMPLETION_REPORT.md`**: Verification report documenting completion of the foundation phase.

---

### `frontend/`

A React 19 single-page application built with Vite, TypeScript, and Tailwind CSS.

- **`package.json`**: Defines frontend dependencies: `react`, `react-dom`, `lucide-react` (icons), `tailwindcss` 4, and dev tooling (`vite`, `typescript`, `oxlint`).
- **`vite.config.ts`**: Vite configuration with `@vitejs/plugin-react` and `@tailwindcss/vite`.
- **`index.html`**: Host HTML page setting meta tags, viewport, and page title.
- **`.env`**: Runtime configuration (`VITE_USE_MOCK=false`, `VITE_API_URL=http://localhost:8000`).
- **`src/types.ts`**: TypeScript type definitions mirroring `backend/shared/schemas.py`.
- **`src/index.css`**: Tailwind base styling, emergency pulse animations, and projector presentation mode rules.
- **`src/main.tsx`**: Bootstraps the React virtual DOM into `#root`.
- **`src/App.tsx`**: Central application state coordinator: connects to SSE, coordinates mode switching, controls the sim clock, manages modals, and renders the 3-column clinical layout.

#### `frontend/src/api/`
- **`client.ts`**: Unified API interface:
  - Fetches tasks, ward overview, patient details, sim state, and eval results.
  - Manages real-time SSE event subscriptions (`tasks_updated`, `ward_updated`, `sim_tick`, `emergency`).
  - Includes an in-memory `MockStore` fallback allowing full interactive testing even when the backend is offline.

#### `frontend/src/components/`
- **`TopBar.tsx`**: App header featuring WardPulse logo, ward details, Naïve AI vs WardPulse toggle, sim clock with play/pause and speed selector, K attention budget selector (`1`, `2`, `3`), language switcher (`EN`, `हिं`, `తె`), and nurse profile.
- **`NavSidebar.tsx`**: Left navigation rail containing **Console** (with active cards badge), **Ward map**, **Handover**, **Protocols**, **Proof**, **How it thinks**, and **Sign In**.
- **`AttentionCards.tsx`**: Main attention console presenting the top K prioritized cards side-by-side:
  - Bed number and rank (e.g. `BED 7 #1`).
  - Action badge (`ESCALATE` in amber, `BEDSIDE ACTION` in purple).
  - Anonymous patient descriptor (e.g. `Bed 7 · Post-op · 28 y/o`).
  - Headline clinical explanation derived from baseline deviations.
  - Key vitals row with baseline comparisons & trend arrows (`HR 108 (base 78) ↑`).
  - `DATA AGE` chips showing freshness per vital parameter.
  - Numbered **DO NOW** protocol checklist with clinical action codes (`A01`, `A02`, `A05`, `A09`).
  - Action buttons: `Page doctor`, `✓ Done`, and local `Snooze ▾`.
- **`RightSidebar.tsx`**: Right control column featuring:
  - Quick action buttons: **Enter vitals** and **I'm worried**.
  - **"WARD AT A GLANCE"** 20-bed interactive grid with status markers (`▲ Crash`, `◆ Active card`, `● Watch`, `● Calm`).
  - **"LIVE PROOF · SAME DATA"** comparison table dynamically computed from real API data.
- **`ReplayTimeline.tsx`**: Bottom interactive timeline with time ticks, scrubber handle, and one-click demo story jump chips (`14:00 Calm ward`, `01:15 Bed 9 cannula`, `02:30 Budget overflow`, `10:30 Bed 12 drifting`, `14:03 Bed 12 crash`).
- **`EmergencyBanner.tsx`**: Full-width urgent red banner alerting to crash bypass events (Bed 12 physiological collapse).
- **`StandbyQueue.tsx`**: Displays ranked cards held in reserve once the K attention budget is filled.
- **`PatientDetailPanel.tsx`**: Slide-over drawer displaying 24-hour vital trends, inline sparklines, and clinical assessments for an inspected bed.
- **`QuickVitalsModal.tsx`**: Bedside dialog allowing nurses to record updated vital signs for any bed.
- **`WorriedModal.tsx`**: Bedside nurse concern dialog allowing qualitative escalation bypassing numerical thresholds.
- **`Placeholders.tsx`**: Clinical placeholder screens for secondary navigation tabs (Ward map layout, SBAR handover summary, protocol action directory, benchmark proof, and algorithm explainers).
- **`Sparkline.tsx`**: Lightweight SVG line chart component rendering vital trend trajectories.
- **`ModeToggle.tsx`**: Interactive comparison toggle showcasing the alarm noise reduction between Naïve NEWS2 and WardPulse.
- **`HelpModal.tsx`**: Clinical reference dialog explaining the dual-horizon personal baseline and attention allocation logic.
- **`DemoBanner.tsx`**: Interactive banner guiding viewers through the 3 clinical demo stories.
- **`Header.tsx`**: Auxiliary top header component.
- **`ActiveCards.tsx`**: Legacy card list component.
- **`WardStrip.tsx`**: Horizontal 20-bed overview strip component.

#### `frontend/src/mock/`
- **`mockData.ts`**: Offline mock dataset representing 20 hospital beds, patient demographics, 24-hour vital history series, and canned evaluation metrics.

---

### `scripts/`

Automated test and launch utilities:

- **`check_stories.py`**: Automated end-to-end integration test. Connects to the running FastAPI server, resets the simulation clock, steps through each scripted scenario timestamp, and programmatically asserts:
  - Story 1: Bed 3 is calm while Bed 7 raises an active card.
  - Story 2: Bed 4 receives `repeat_bp` rather than an inappropriate doctor page.
  - Story 3: Bed 12 triggers the emergency crash banner while active cards remain bounded to K=2.
- **`run_all.ps1`**: Windows PowerShell launcher that seeds the database, starts the FastAPI backend on port 8000, and starts the Vite frontend on port 5173.
- **`run_all.sh`**: Linux/macOS Bash launcher executing the same unified startup flow.
- **`run_backend.ps1`**: Windows PowerShell helper starting only the FastAPI backend server.
- **`run_backend.sh`**: Linux/macOS Bash helper starting only the FastAPI backend server.
