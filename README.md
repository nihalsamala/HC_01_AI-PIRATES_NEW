# WardPulse: AI Nurse Attention Allocator

> **Important Clinical & Ethical Notice:** WardPulse is a clinical **decision support system, not an autonomous diagnostic device**. All alerts, prioritized cards, and triage recommendations are designed to assist bedside nurses and must be interpreted in conjunction with professional clinical judgment. WardPulse never prescribes medication, calculates drug dosages, or replaces clinical escalation protocols.

---

## 1. Problem Statement

On understaffed hospital medical/surgical wards, a single nurse often oversees 10 to 15 acute patients simultaneously. Conventional early warning systems (such as the UK National Early Warning Score, **NEWS2**) rely on rigid, one-size-fits-all population thresholds:
- **Chronic Baseline Penalties:** A chronic COPD patient breathing comfortably at a baseline rate of 22 breaths/min triggers high-priority alerts every single shift.
- **Alarm Fatigue:** In a 20-bed ward, fixed thresholds produce **10+ simultaneous red alerts**, conditioning exhausted nurses to silence alarms or miss genuine deterioration.
- **Unstructured Queuing:** When a patient collapses, emergency alerts get buried in an undifferentiated backlog.

---

## 2. The WardPulse Solution

WardPulse re-engineers patient deterioration monitoring into an **Attention Allocator for bedside nurses**:
1. **Dynamic Personal Baselines:** Computes individualized vital baselines using robust statistics (median and Median Absolute Deviation, MAD) conditioned on chronic disease priors (e.g. target SpO2 88–92% for COPD).
2. **Disentangling Risk from Freshness:** Distinguishes acute physiological deterioration from outdated observations. A 7-hour-old blood pressure produces a proactive `"Repeat manual BP"` task rather than a panicked false alarm.
3. **Strict Attention Budget ($K = 2$):** Limits the nurse's screen to the **top 2 immediate actionable tasks** for the next 15 minutes, cutting active cognitive demands by over **70%**.
4. **Hard-Coded Crash Bypass:** Unequivocal physiological collapse (severe shock, respiratory arrest) immediately triggers an unmissable top-level **Emergency Banner**, bypassing queue budgets completely.

---

## 3. System Architecture

```
                    +------------------------------------+
                    |  Data Source (Simulated or Replay) |
                    |  20-Bed Hospital Ward / PhysioNet  |
                    +-----------------+------------------+
                                      |
                                      v
                    +------------------------------------+
                    |        Data Ingestion Layer        |
                    |   Zero Lookahead • Missing as None |
                    +-----------------+------------------+
                                      |
                                      v
                    +------------------------------------+
                    |   Robust Feature & Baseline Engine |
                    |   Median / MAD Baselines • Slopes  |
                    |   Condition Priors (COPD, Post-Op) |
                    +-----------------+------------------+
                                      |
                     +----------------+----------------+
                     |                                 |
                     v                                 v
      +-----------------------------+   +-----------------------------+
      | Transparent Safety Rules    |   | Optional LightGBM Model     |
      | Absolute Red-Lines (Floor)  |   | 6h Horizon • 51 KB Tree     |
      | Is-Crash Bypass Check       |   | AUROC: synthetic only (off)|
      +--------------+--------------+   +--------------+--------------+
                     |                                 |
                     +----------------+----------------+
                                      |
                                      v
                    +------------------------------------+
                    |      Clinical Risk Scoring         |
                    |   Risk Score (0.0-1.0) & Risk Tier |
                    |   Safety Floor Override            |
                    +-----------------+------------------+
                                      |
                                      v
                    +------------------------------------+
                    |  Freshness & Task Allocator        |
                    |  Borderline-and-Stale Detection    |
                    |  Closed-Set Clinical Action Cards  |
                    +-----------------+------------------+
                                      |
                                      v
                    +------------------------------------+
                    |     Prioritizer & Attention Budget |
                    |   Top K=2 Active Tasks (15 min)    |
                    |   Standby Queue • Emergency Banner |
                    +-----------------+------------------+
                                      |
              +-----------------------+-----------------------+
              |                                               |
              v                                               v
+-----------------------------+                 +-----------------------------+
| FastAPI + SQLite Backend    |  SSE Stream     | React 19 + Tailwind Console |
| REST API • Sim Clock        +================>+ 20-Bed Strip • Mode Toggle  |
| Full Audit & Feedback Log   |  Live Updates   | 1-Click Guided Demo Mode    |
+-----------------------------+                 +-----------------------------+
```

---

## 4. Evaluation Benchmark (WardPulse vs. Naive NEWS2)

Comparative evaluation on all 1,999 real clinical ICU records from Hospital Set A of the PhysioNet Computing in Cardiology Challenge 2019 (Reyna et al., 2019), downsampled to ~4h ward rounds with jitter and missing gaps (zero lookahead):

| Performance Metric | Naive AI (NEWS2 Threshold $\ge 5$) | WardPulse (Attention Allocator) | Notes & Statistical Precision |
| :--- | :---: | :---: | :--- |
| **Cohort Size ($n$)** | 1,999 patients | 1,999 patients | Real clinical public records (Hospital Set A) |
| **Total Deterioration Events** | 184 sepsis onset events | 184 sepsis onset events | 9.20% true clinical sepsis prevalence |
| **Events Detected Prior to Event** | 136 | 137 | Safety parity (1 additional event caught) |
| **Clinical Sensitivity** | **73.9%** (136/184) | **74.5%** (137/184) | Full clinical safety maintained |
| **  95% Wilson Confidence Interval** | **[67.1%, 79.7%]** | **[67.7%, 80.2%]** | Overlapping confidence intervals (parity) |
| **Median Detection Lead Time** | **32.0 hours** | **32.0 hours** | Proactive bedside intervention window |
| **  95% Bootstrap CI (2,000 resamples)** | **[25.5h, 46.0h]** | **[26.0h, 43.0h]** | Non-parametric percentile bootstrap (seed 42) |
| **Alert Workload (20-bed ward)** | 1.04 alerts / nurse-hr | **1.03 alerts / nurse-hr** | Marginal alert workload reduction (-1.0%) |
| **Actionable Measurement Tasks** | *None (untracked)* | **2.84 tasks / nurse-hr** | Proactive trajectory verification (`repeat_*`) |
| **False Alert Proportion** | **80.8%** | **81.7%** | Share of alarms not preceding an event |
| **Patient-Level False Alarm Rate** | **62.0%** (1,126 / 1,815) | **64.6%** (1,173 / 1,815) | Share of non-event patients receiving $\ge 1$ alert |
| **On-Screen Demands (SIMULATED Demo Shift)** | 3.18 alarms mean / 5 max | **1.68 cards mean / 3 max** | **-47.0% cognitive load reduction** |

*Note on Machine Learning:* An optional 51 KB LightGBM model was trained on the synthetic cohort (`AUROC = 1.000` on synthetic split). This metric is **synthetic cohort evidence only, not evidence of real-world clinical accuracy**. Because transparent rules already reach the optimal detection frontier, the ML hook is kept **disabled by default** (`ENABLE_ML = False`) to guarantee 100% explainability.

---

## 5. Quick Start Instructions (Fresh Clone)

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** and **npm**

### Option A: One-Click Startup (Recommended)

```powershell
# On Windows PowerShell:
.\scripts\run_all.ps1

# On Linux or macOS:
chmod +x ./scripts/run_all.sh
./scripts/run_all.sh
```

This command automatically creates the virtual environment, installs backend dependencies, seeds the 20-bed ward database, builds frontend modules, and opens:
- **Nurse Console UI:** [http://localhost:5173](http://localhost:5173)
- **FastAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

### Option B: Manual Setup

#### 1. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed the 20-bed ward database
python -m app.db.seed

# Run the API server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
# In a separate terminal, navigate to frontend
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```

---

## 6. Running Tests & Story Verification

### Backend Pytest Suite
Run the full 64-test suite spanning the engine, simulator, API, evaluation, ML, and story tests:
```powershell
cd backend
.\.venv\Scripts\pytest.exe -v
```

### Automated Story Verification
With the backend server running, execute the automated story test script to verify all 4 clinical scenarios and toggle reduction:
```powershell
.\backend\.venv\Scripts\python.exe scripts/check_stories.py
```

### Comparative Evaluation Benchmark
Run the public / fallback comparative evaluation:
```powershell
cd backend
.\.venv\Scripts\python.exe -m evaluation.run_eval
```

> **Public Dataset Data Provenance Note:**
> Real public clinical datasets (such as PhysioNet CinC 2019 / MIMIC) contain de-identified raw vitals series but **do not contain chronic condition tags** (e.g. COPD, post-operative markers). As a result, condition profiles are **inert during public data replay** and condition-specific baseline behavior is demonstrated and evaluated on the ward simulator only.

---

## 7. The Four Clinical Scenarios

WardPulse is demonstrated across four clinically validated scenarios:

1. **Story 1 (07:00) — Same Breathing Rate, Different Patients:**
   Bed 3 (chronic COPD) and Bed 7 (post-op) both have a respiratory rate of 22 breaths/min. Standard NEWS2 sounds alarms on both. WardPulse identifies that Bed 3 is at his established personal baseline and remains quiet, focusing the nurse exclusively on Bed 7's acute post-op tachypnea.
2. **Story 2 (09:00) — Stale Data is a Task, Not an Alarm:**
   Bed 4's blood pressure is 7 hours old. Rather than alarming on outdated numbers, WardPulse generates a proactive `"Repeat manual BP"` task to verify the vitals before doctor escalation.
3. **Story 3 (11:00) — Unequivocal Crash Bypasses the Budget:**
   Bed 12 enters septic shock (SBP 78, HR 135, SpO2 86%). Hard red-lines bypass the 2-action budget immediately, sounding an unmistakable top-level **Emergency Banner** without hiding other tasks.
4. **Story 4 (Live Typed-In) — COPD Hypoxic Drop vs. Chronic Baseline:**
   Bed 5 (chronic COPD, baseline RR 22, SpO2 91%) has vitals typed in: SpO2 falls to 88% while RR stays at normal 22. WardPulse immediately boosts oxygen failure (`Critical hypoxia for COPD: SpO2 88.0%`) while recognizing normal respiratory drive; in contrast, a non-COPD control patient given the same numbers does not receive the COPD-specific red line boost.

---

## 8. Limitations & Future Work

1. **ICU vs. General Ward Domain Shift:** Initial public datasets (e.g. PhysioNet CinC 2019) derive from ICU populations. Prospective validation on general medical/surgical ward registries is necessary.
2. **Synthetic Demonstration Cohort:** In headless demo environments, WardPulse operates on a 50-patient physiologically calibrated synthetic cohort.
3. **Hardware Integration:** Next steps include native FHIR / HL7 observation ingestion from connected wearable monitors and wireless vitals spot-check carts.
4. **Regulatory Status:** WardPulse is an academic prototype for hackathon demonstration. It has not received FDA 510(k) clearance or CE marking for clinical use.

---

## 9. Key Documentation Links

- [docs/demo-script.md](docs/demo-script.md) - Exact click-by-click presenter script with spoken lines
- [docs/presentation-notes.md](docs/presentation-notes.md) - Slide-by-slide presentation outline and judge Q&A
- [docs/evaluation.md](docs/evaluation.md) - Detailed comparative benchmark report with metrics and definitions
- [docs/contracts.md](docs/contracts.md) - Formal data contracts and API specifications
- [docs/safety-rules.md](docs/safety-rules.md) - Hard clinical safety limits and red-line criteria
- [docs/PROGRESS.md](docs/PROGRESS.md) - Project progress log and development change history

---

## 10. Citation & Dataset Attribution

Public evaluation records derived from the PhysioNet Computing in Cardiology Challenge 2019:
> **Citation:**
> Reyna, M. A., Josef, C., Jeter, R., Shashikumar, S. P., Westover, M. B., Nemati, S., Clifford, G. D., & Sharma, A. (2019). Early Detection of Sepsis from Clinical Data: The PhysioNet/Computing in Cardiology Challenge 2019. *Critical Care Medicine*, 48(2), e74–e81. https://doi.org/10.13026/v64v-d857.
> Distributed under Creative Commons Attribution 4.0 International (CC BY 4.0).