# WardPulse Clinical Safety Rules & Physiological Limits

> **Clinical Disclaimer:** The thresholds, condition-based priors, and safety limits documented here are designed for decision support and demonstration within the hackathon prototype. Before deployment in live patient care, all values and card wordings MUST be formally reviewed and ratified by a clinician or nursing specialist.

---

## 1. NEWS2 Reference and Official Citation

WardPulse benchmarks against the official **National Early Warning Score 2 (NEWS2)** established by the Royal College of Physicians (London, UK):

> **Citation:**
> Royal College of Physicians. *National Early Warning Score (NEWS) 2: Standardising the assessment of acute-illness severity in the NHS*. Updated report of a working party. London: RCP, 2017.

### Standard RCP NEWS2 Scoring Matrix

| Physiological Parameter | Score 3 | Score 2 | Score 1 | Score 0 | Score 1 | Score 2 | Score 3 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Respiration Rate (bpm)** | $\le 8$ | | 9–11 | 12–20 | | 21–24 | $\ge 25$ |
| **SpO2 Scale 1 (%)** | $\le 91$ | 92–93 | 94–95 | $\ge 96$ | | | |
| **SpO2 Scale 2 (COPD Target 88-92%)** | $\le 83$ | 84–85 | 86–87 | 88–92 (on air) | 93–94 on O2 | 95–96 on O2 | $\ge 97$ on O2 |
| **Air or Oxygen** | | Oxygen | | Air | | | |
| **Systolic BP (mmHg)** | $\le 90$ | 91–100 | 101–110 | 111–219 | | | $\ge 220$ |
| **Pulse (bpm)** | $\le 40$ | | 41–50 | 51–90 | 91–110 | 111–130 | $\ge 131$ |
| **Consciousness (ACVPU)** | | | | Alert (A) | | | C, V, P, or U |
| **Temperature (°C)** | $\le 35.0$ | | 35.1–36.0 | 36.1–38.0 | 38.1–39.0 | $\ge 39.1$ | |

---

## 2. Hard Clinical Red Lines

A central safety rule in WardPulse is that **a personal baseline may reduce a false alarm ONLY within safe physiological boundaries and must NEVER hide or soften an absolute red-line breach**.

Hard red lines fire when:
1. **Any individual physiological parameter reaches maximum NEWS2 score (3)**:
   - Respiration rate $\le 8$ or $\ge 25$ breaths/min
   - Oxygen saturation $\le 91\%$ on room air (or $\le 88\%$ for patients with documented COPD target 88–92%)
   - Systolic BP $\le 90$ or $\ge 220$ mmHg
   - Pulse rate $\le 40$ or $\ge 131$ bpm
   - Altered consciousness (Confusion, Voice, Pain, Unresponsive)
   - Temperature $\le 35.0^\circ\text{C}$ or $\ge 39.1^\circ\text{C}$
2. **Aggregate NEWS2 Score reaches High Clinical Risk**:
   - Total NEWS2 score $\ge 7$.

When any hard red line is breached, WardPulse guarantees that the calculated risk score is immediately elevated to at least `RiskTier.HIGH` (score $\ge 0.60$) and cannot be suppressed by personal baseline familiarity.

---

## 3. Unequivocal Crash Definition (Crash Bypass)

Crash vitals represent immediate, life-threatening physiological decompensation that requires immediate medical presence, bypassing the nurse's $K=2$ attention inbox directly to a top-of-screen emergency banner:

1. **Severe Shock (Hypotension + Tachycardia)**:
   - Systolic BP $\le 80\text{ mmHg}$ **AND** Heart Rate $\ge 130\text{ bpm}$ (Story 3 criteria: SBP 78, HR 135).
2. **Hypotension with Severe Hypoxia**:
   - Systolic BP $\le 80\text{ mmHg}$ **AND** $\text{SpO}_2 \le 88\%$.
3. **Profound Hypotensive Collapse**:
   - Systolic BP $\le 70\text{ mmHg}$.
4. **Profound Hypoxic Collapse**:
   - $\text{SpO}_2 \le 82\%$.
5. **Extreme Tachycardia with Cognitive Decline**:
   - Heart Rate $\ge 140\text{ bpm}$ **AND** altered consciousness ($\text{ACVPU} \ne \text{A}$).

---

## 4. Condition-Based Clinical Priors

When a patient is admitted with sparse or no vitals history ($n < 3$ readings), WardPulse blends observed values toward a condition-specific prior:

| Condition Prior | HR (bpm) | SBP (mmHg) | DBP (mmHg) | RR (bpm) | SpO2 (%) | Temp (°C) | Rationale |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **COPD** | 80 | 125 | 78 | 21.5 | 91.0 | 36.8 | Compensatory tachypnea and baseline hypoxemia are physiological normals in severe chronic airflow limitation. |
| **Post-Op** | 76 | 120 | 76 | 14.5 | 97.5 | 36.9 | Recovering from surgical anesthesia; expected normal respiratory drive with mild post-operative sympathetic recovery. |
| **Cardiac** | 96 | 148 | 90 | 17.0 | 96.0 | 36.7 | Chronic cardiovascular disease patients often maintain higher baseline blood pressure and mild resting tachycardia. |
| **General** | 72 | 120 | 76 | 15.0 | 98.0 | 36.7 | Standard adult reference ranges. |

---

## 5. Floor Spread Values

To prevent mathematical division by zero when calculating deviation $z$-scores on patients with stable identical repeated vitals, WardPulse enforces non-zero spread floors:
- Heart Rate: $5.0\text{ bpm}$
- Systolic BP: $6.0\text{ mmHg}$
- Diastolic BP: $5.0\text{ mmHg}$
- Respiratory Rate: $1.5\text{ bpm}$
- $\text{SpO}_2$: $1.0\%$
- Temperature: $0.2^\circ\text{C}$

---

## 6. Condition Profiles & Pattern Rules

> **Clinical Status: Placeholder, needs clinical review.**
> All condition profile weights, vital sign focus mappings, and pattern definitions documented below are initial prototypes designed for decision support demonstration. They MUST undergo formal clinical and nursing review before any operational ward deployment.

### Clinical Weighting Principles:
1. **Weights ONLY Boost, Never Mute:**
   Condition-specific profile weights are strictly asymmetrical: they **only boost sensitivity** to deteriorating patterns in organs vulnerable to the patient's condition; they **never mute, suppress, or discount** signs of physiological decompensation.
2. **Red Lines Remain Inviolable:**
   Hard clinical safety red lines (Section 2) and unequivocal crash criteria (Section 3) are completely unalterable and apply universally regardless of patient condition tags or profile weights. A red-line breach always overrides all baseline adjustments and forces high risk.
3. **Condition Profiles and Focus Vitals:**
   - **COPD Profile:** Focus vitals: $\text{SpO}_2$ and $\text{RR}$. Chronic compensatory tachypnea (e.g. RR 21–23) with stable saturations does not trigger alarms, but hypoxic deviation below personal baseline or breaching $\text{SpO}_2 \le 88\%$ immediately triggers acute escalation (`Critical hypoxia for COPD`).
   - **Post-Op Profile:** Focus vitals: $\text{RR}$ and $\text{HR}$. Elevated vigilance for respiratory depression (opioid-induced hypoventilation) and sympathetic tachycardia (early bleeding or septic drift).
   - **Cardiac Profile:** Focus vitals: $\text{HR}$ and $\text{SBP}$. Heightened vigilance for arrhythmic rate spikes, decompensated hypertension, or cardiogenic pressure drop.

---

## 7. Data Provenance & Public Dataset Limitations

Public clinical benchmark records (e.g. PhysioNet Computing in Cardiology 2019 / MIMIC) contain de-identified physiological time series but **do not include chronic condition ICD tags** (such as confirmed COPD, post-operative status, or specific cardiac histories). 

Consequently:
- Condition profiles and condition-based focus vitals are **completely inactive during evaluation replay on public datasets** (falling back to the general population baseline).
- Condition-specific behavior, personal baseline discrimination (Story 1), and typed-in targeted deterioration (Story 4) are **demonstrated and evaluated on the simulator only**.
- Benchmark headline numbers on the public dataset remain 100% stable and unperturbed by condition-specific profile additions.

