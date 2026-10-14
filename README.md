# WardPulse

> **Important Notice:** WardPulse provides clinical decision support, not medical diagnosis. All recommendations are designed to assist nursing workflows and must be exercised in accordance with professional clinical judgment.

WardPulse is an AI early warning system for patient deterioration designed for understaffed hospital general wards.
Instead of bombarding staff with raw scores, WardPulse operates as a Nurse Attention Allocator.
It analyzes sparse vitals against personal baselines and distinguishes clinical risk from data freshness.
A strict attention budget (K=2) highlights the top 2 immediate nursing actions for the next 15 minutes to eliminate alarm fatigue.
Unequivocal crash vitals bypass the queue to trigger immediate emergency clinical escalation.

---

## Quick Start

### Backend
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv backend/.venv
   # Windows PowerShell:
   .\backend\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source backend/.venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Start the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
   Or run the helper scripts: `./scripts/run_backend.sh` or `.\scripts\run_backend.ps1`.
   Check health status at [http://localhost:8000/health](http://localhost:8000/health).

### Frontend
- Frontend console in React + Vite + TypeScript + Tailwind (placeholder: to be added in work package P5).

---

## Running Tests

From the `backend/` directory:
```bash
cd backend
pytest
```

---

## Repository Structure

```
├── AGENTS.md                   # Instructions and rules for AI coding agents
├── README.md                   # Project overview and quick start guide
├── .gitignore                  # Git ignore rules
├── docs/                       # Project documentation
│   ├── PROJECT_CONTEXT.md      # Domain problem, design decisions, and system architecture
│   ├── contracts.md            # Inter-module data schemas and contracts
│   ├── PROGRESS.md             # Work package statuses and progress log
│   └── AGENT_PROMPTS.md        # Work package prompts for agent tasks
├── backend/
│   ├── requirements.txt        # Backend Python dependencies
│   ├── shared/                 # Shared data shapes and schemas (contracts in code)
│   ├── app/                    # FastAPI application, routes, and database models
│   ├── engine/                 # Core WardPulse attention allocation & NEWS2 logic
│   ├── simulator/              # Ward simulation clock and scenario vitals generator
│   ├── evaluation/             # Dataset replay and comparative benchmark harness
│   ├── ml/                     # Machine learning models (LightGBM)
│   └── tests/                  # Test suites
├── data/
│   ├── sample/                 # Sample data for testing and demonstrations
│   └── raw/                    # Raw datasets (excluded from version control)
└── scripts/                    # Convenience scripts for running services
```

---

## Team Workflow

All team members and agents follow structured workflows:
- Run all tests before committing.
- Commit in small, logical increments with semantic prefixes:
  - `contract:` Schema or contract updates
  - `engine:` Core engine logic
  - `sim:` Simulator logic and scenarios
  - `eval:` Evaluation harness and metrics
  - `ml:` Machine learning models
  - `api:` FastAPI and database code
  - `ui:` Frontend React console
  - `docs:` Documentation updates
  - `chore:` Tooling, scaffolding, and skeleton tasks
- Always rebase before pushing: `git pull --rebase` followed by `git push`.
- Update `docs/PROGRESS.md` after completing each work package.

---

## Documentation Links

- [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) - Problem statement, architectural decisions, and clinical background
- [docs/contracts.md](docs/contracts.md) - Exact data contracts and API specifications
- [docs/PROGRESS.md](docs/PROGRESS.md) - Current status of all packages and change log
- [docs/AGENT_PROMPTS.md](docs/AGENT_PROMPTS.md) - Agent task definitions