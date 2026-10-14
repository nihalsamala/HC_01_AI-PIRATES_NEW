# WardPulse: Evidence Pack & Presentation Numbers

This document provides the definitive, empirically measured evidence table for the WardPulse hackathon jury defense and presentation.

> **Integrity Guarantee:** Every number in this document was measured directly through executable benchmarks without manual estimation or rounding manipulation. "NOT MEASURED" is explicitly declared for metrics unsupported by baseline architectures.

---

## 1. Master Evidence Table

| Metric | WardPulse | NEWS2 (Comparator) | How Measured | Data Source | Command to Reproduce |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Clinical Sensitivity (Event Detection)** | **87.5%** (14/16) | **87.5%** (14/16) | Zero lookahead walk across patient timelines; alert raised $\le t_{\text{event}}$ | Synthetic (50-patient calibrated fallback cohort) | `python -m evaluation.run_eval` |
| **Median Detection Lead Time** | **2.0 hours** | **2.0 hours** | Median hours from first alert to documented event onset ($t_{\text{event}}$) | Synthetic (50-patient cohort) | `python -m evaluation.run_eval` |
| **Cohort Alert Rate (Workload)** | **1.15** alerts/nurse-hr | **1.17** alerts/nurse-hr | Alerts raised scaled to 20-bed ward divided by total observation hours | Synthetic (50-patient cohort) | `python -m evaluation.run_eval` |
| **Cohort False Alert Ratio** | **86.0%** | **86.2%** | Unactionable alerts (stable cases or post-event) divided by total alerts | Synthetic (50-patient cohort) | `python -m evaluation.run_eval` |
| **Cohort Triage Measurement Tasks** | **0.15** tasks/nurse-hr | **NOT MEASURED** *(unsupported)* | Recheck tasks (`repeat_*`, `full_vitals`) generated on borderline-stale vitals | Synthetic (50-patient cohort) | `python -m evaluation.run_eval` |
| **Story 1 Alerts on Screen (07:00:00)** | **1 card** (Bed 7 active) | **2 alerts** (Bed 7 + Bed 3) | Alerts on screen at +1h; Bed 3 (COPD RR 22) quiet vs Bed 7 (Post-op RR 22) | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Story 2 Alerts on Screen (09:00:00)** | **2 cards** (Beds 7 & 4) | **3 alerts** (threshold alarms) | Alerts on screen at +3h; Bed 4 gets `repeat_bp` on stale BP, filling K=2 | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Story 3 Alerts on Screen (11:00:00)** | **3 cards** (1 emergency + 2) | **5 alerts** (alarm flood) | Alerts on screen at +5h; Bed 12 crash bypass SBP 78 + 2 active cards | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Mean Alerts on Screen (6h Demo Window)** | **1.68 cards** | **3.18 alerts** | Average on-screen active demands sampled at 5-minute intervals (06:00–12:00) | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **On-Screen Cognitive Load Reduction (6h)** | **-47.0%** | *Baseline (High Fatigue)* | Reduction in mean on-screen demands during the core clinical demo window | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Mean Alerts on Screen (12h Shift)** | **2.34 cards** | **2.92 alerts** | Average on-screen active demands across 145 discrete 5-min evaluations | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Max Concurrent Alerts on Screen** | **3 cards** (K=2 + 1 crash) | **5 alerts** | Maximum simultaneously demanding cards at any point during 12h shift | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **New Distinct Alert Events (12h Shift)** | **4 alerts** | **6 alerts** | Unique alert activation episodes throughout 12h shift across 20 beds | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Alert Rate (1 Nurse covering 20 beds)** | **0.33** alerts/nurse-hr | **0.50** alerts/nurse-hr | New alert events divided by 12 nurse-hours | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Alert Rate (2 Nurses covering 20 beds)** | **0.17** alerts/nurse-hr | **0.25** alerts/nurse-hr | New alert events divided by 24 nurse-hours | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Triage Measurement Tasks Created (Shift)** | **1 task** (Bed 4 `repeat_bp`) | **NOT MEASURED** *(unsupported)* | Actionable measurement tasks generated to verify stale data | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Full Ward Evaluation Latency (Median)** | **1.38 ms** | **0.42 ms** | Pure logic CPU execution time across all 20 beds (median over 100 runs) | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **Full Ward Evaluation Latency (p95)** | **2.05 ms** | **0.72 ms** | 95th percentile execution time across 20 beds over 100 runs | Synthetic (20-bed simulator ward, seed 42) | `python scripts/measure_demo.py` |
| **COPD Cohort Alert Rate (NEWS2 Scale 1)** | **0.33** alerts/nurse-hr | **3.67** alerts/nurse-hr | Evaluated on chronic COPD patients; standard default NEWS2 chart (Scale 1) | Synthetic (ablation study across 4 seeds) | `python -m evaluation.ablation` |
| **COPD Cohort Alert Rate (NEWS2 Scale 2)** | **0.33** alerts/nurse-hr | **1.00** alerts/nurse-hr | Evaluated on chronic COPD patients; dedicated 88–92% target chart (Scale 2) | Synthetic (ablation study across 4 seeds) | `python -m evaluation.ablation` |
| **Pytest Test Suite Pass Count** | **64 passed** (0 failed) | Integrated in tests | Full automated test suite across 9 test files | Unit, engine, contract, api, eval tests | `pytest` |
| **Repository Commit Count** | **39 commits** | N/A | Total revision history depth on `main` branch | Git repository history | `git rev-list --count HEAD` |

---

## 2. Test Files Inventory (64 Total Tests Passed)

| Test File | Test Count | Scope Verified |
| :--- | :---: | :--- |
| `backend/tests/test_api.py` | 14 | All 12 FastAPI endpoints, CORS, database models, session management, and SSE stream |
| `backend/tests/test_engine_a.py` | 8 | Features, robust median/MAD baselines, red lines, crash bypass, and NEWS2 scoring |
| `backend/tests/test_engine_b.py` | 9 | Freshness rules, task generation from closed set, K=2 prioritizer, and aging |
| `backend/tests/test_evaluation.py` | 5 | Dataset loader, downsampling with jitter/gaps, metrics calculation, and zero lookahead |
| `backend/tests/test_ml.py` | 6 | Tabular vectorizer, LightGBM inference, NaN handling, and safety floor override |
| `backend/tests/test_schemas_smoke.py` | 6 | Pydantic schema validation, enums, closed task set, and default configurations |
| `backend/tests/test_simulator.py` | 9 | Deterministic 20-bed ward generator, clock advancement, and 3 canonical demo stories |
| `backend/tests/test_simulator_real.py` | 5 | Source="replay" de-identified trajectory loader, story overlays, and toggle noise reduction |
| `backend/tests/test_story4_copd.py` | 2 | Live Story 4 fixture: Bed 5 COPD hypoxia boost vs Bed 6 control discrimination |
| **Total** | **64 passed** | **0 failed across all modules** |

---

## 3. Important Methodological Caveats

1. **ICU Data Thinned to Ward Cadence:**
   Public clinical records (such as the PhysioNet CinC 2019 sepsis benchmark) originate from Intensive Care Unit (ICU) populations with continuous monitoring. To reflect general hospital medical/surgical wards realistically, records were downsampled to 4–6 hour observation intervals with jitter and missing data gaps. True prospective performance should be confirmed on dedicated general ward cohorts.
2. **Simulated Demo Ward:**
   The interactive 20-bed demo ward operates on a deterministic simulator with calibrated clinical priors (COPD, post-op, cardiac). While physiology is modeled on published clinical literature (e.g., RCP NEWS2 and British Thoracic Society guidelines), it represents simulated validation rather than hospital electronic health record (EHR) data.
3. **Decision Support, Not Autonomous Medical Device:**
   WardPulse is an academic proof-of-concept designed as a nurse attention allocator. It does not prescribe therapeutics, calculate medication dosages, or replace registered clinician judgment.
