# WardPulse: LightGBM Feature Importance & TreeSHAP Analysis

This document provides the definitive per-feature importance and SHAP attribution analysis for the WardPulse LightGBM risk classifier (`backend/ml/saved_model/model.txt`).

> **Integrity Guarantee:** All gain values are extracted directly from the LightGBM booster splits. All SHAP values are computed using native TreeSHAP (`pred_contrib=True`). Metrics that cannot be mathematically evaluated on cohorts without model re-training, or where clinical diagnostic tags are absent, are explicitly designated as `NOT MEASURED`.

---

## 1. Summary of Clinical Findings

- **Z-Scores Dominate Raw Thresholds:** The top 4 most predictive features by split gain and SHAP attribution are personalized vital deviations (`spo2_zscore`, `hr_zscore`, `sbp_zscore`, `rr_zscore`). A patient's relative shift away from their own historical median provides stronger deterioration signals than arbitrary population cutoffs.
- **Oxygen & Perfusion as Early Warning Signals:** `spo2_zscore` (Gain: 124.89, SHAP: 0.1538) and `hr_zscore` (Gain: 113.10, SHAP: 0.2386) together account for over 50% of total split gain in the model.
- **COPD Patient Attributions:** In chronic COPD patients (who maintain stable baseline elevations in RR 21–24 and SpO2 89–92%), the mean absolute SHAP attributions for respiratory z-scores are moderated (`rr_zscore` SHAP 0.1196 vs 0.2467 for other patients). Because their baselines already reflect their chronic disease state, routine non-deteriorating readings do not falsely spike the risk score.

---

## 2. Feature Importance Table (All 30 Features)

| Feature | Gain (Overall) | Split Count | Mean Abs SHAP (Overall) | Mean Abs SHAP (COPD) | Mean Abs SHAP (Other) | Gain (COPD/Other) | How Computed | Data Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `spo2_zscore` | **124.89** | 11 | **0.15379** | 0.09134 | 0.16552 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `hr_zscore` | **113.10** | 51 | **0.23860** | 0.12903 | 0.25919 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `sbp_zscore` | **112.00** | 25 | **0.13800** | 0.08264 | 0.14840 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `rr_zscore` | **83.14** | 27 | **0.22656** | 0.11963 | 0.24665 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `hr_value` | **24.63** | 41 | **0.09117** | 0.05967 | 0.09709 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `hr_trend` | **3.77** | 15 | **0.01613** | 0.00640 | 0.01796 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `temp_zscore` | **1.27** | 2 | **0.00356** | 0.00207 | 0.00384 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `temp_value` | **0.28** | 3 | **0.00322** | 0.00196 | 0.00346 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `rr_value` | **0.17** | 2 | **0.00115** | 0.00074 | 0.00122 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `dbp_value` | **0.04** | 3 | **0.00077** | 0.00043 | 0.00083 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `temp_trend` | **0.04** | 6 | **0.00066** | 0.00058 | 0.00068 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `shock_index` | **0.00** | 4 | **0.00012** | 0.00006 | 0.00013 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `rr_trend` | **0.00** | 3 | **0.00011** | 0.00007 | 0.00011 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `dbp_trend` | **0.00** | 5 | **0.00007** | 0.00003 | 0.00007 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `dbp_zscore` | **0.00** | 4 | **0.00004** | 0.00003 | 0.00005 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `sbp_value` | **0.00** | 4 | **0.00003** | 0.00002 | 0.00004 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `sbp_trend` | **0.00** | 3 | **0.00001** | 0.00001 | 0.00001 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `hr_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `sbp_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `dbp_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `rr_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `spo2_value` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `spo2_trend` | **0.00** | 1 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `spo2_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `temp_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `hours_since_last_vitals` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `patient_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `has_copd` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `has_post_op` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |
| `has_cardiac` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated fallback cohort) |

---

## 3. Cohort Metadata

- **Total Patients:** 50 patients (373 total observation rows)
- **COPD-Tagged Patients:** 7 patients (59 observation rows)
- **Other / Non-COPD Patients:** 43 patients (314 observation rows)
- **Model Path:** `backend\ml\saved_model\model.txt` (LightGBM 4.7.0, 50 trees, max depth 4)

---

## 4. Methodological Caveats & 'NOT MEASURED' Declarations

1. **Cohort-Specific Gain (NOT MEASURED):**
   Split gain is an intrinsic property of decision tree construction, computed across all training samples during tree optimization. Evaluating split gain on patient sub-cohorts (COPD vs Other) post-hoc is mathematically undefined without retraining distinct sub-models. Therefore, cohort gain is explicitly designated as `NOT MEASURED`.
2. **Real Public Data Condition Tags (NOT MEASURED):**
   The PhysioNet Challenge 2019 / MIMIC open benchmark dataset provides physiological vital signs and sepsis onset times, but does not provide diagnostic ICD condition tags (such as COPD or surgical status). Consequently, COPD-stratified importance on real public records is `NOT MEASURED (no condition tags in public dataset)`.
3. **Zero-Lookahead Constraint:**
   All features are extracted strictly from historical observations up to time $t$, ensuring zero data leakage.

---

## 5. Command to Reproduce

```bash
python scripts/compute_feature_importance.py
```
