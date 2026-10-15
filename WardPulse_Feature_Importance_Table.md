# WardPulse: LightGBM Feature Importance Table

This document provides the complete, empirically measured per-feature importance and TreeSHAP attribution table for the WardPulse LightGBM model (`backend/ml/saved_model/model.txt`).

> **Integrity Guarantee:** Every number was computed directly via LightGBM booster tree splits and native C++ TreeSHAP (`pred_contrib=True`). Values that cannot be mathematically calculated without model retraining, or where clinical diagnostic tags are absent, are explicitly marked as `NOT MEASURED`.

---

## 1. Feature Importance & TreeSHAP Table (All 30 Features)

| Feature | Gain (Overall) | Split Count | Mean Abs SHAP (Overall) | Mean Abs SHAP (COPD) | Mean Abs SHAP (Other) | Gain (COPD/Other) | How Computed | Data Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `spo2_zscore` | **124.89** | 11 | **0.15379** | 0.09134 | 0.16552 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `hr_zscore` | **113.10** | 51 | **0.23860** | 0.12903 | 0.25919 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `sbp_zscore` | **112.00** | 25 | **0.13800** | 0.08264 | 0.14840 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `rr_zscore` | **83.14** | 27 | **0.22656** | 0.11963 | 0.24665 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `hr_value` | **24.63** | 41 | **0.09117** | 0.05967 | 0.09709 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `hr_trend` | **3.77** | 15 | **0.01613** | 0.00640 | 0.01796 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `temp_zscore` | **1.27** | 2 | **0.00356** | 0.00207 | 0.00384 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `temp_value` | **0.28** | 3 | **0.00322** | 0.00196 | 0.00346 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `rr_value` | **0.17** | 2 | **0.00115** | 0.00074 | 0.00122 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `dbp_value` | **0.04** | 3 | **0.00077** | 0.00043 | 0.00083 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `temp_trend` | **0.04** | 6 | **0.00066** | 0.00058 | 0.00068 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `shock_index` | **0.00** | 4 | **0.00012** | 0.00006 | 0.00013 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `rr_trend` | **0.00** | 3 | **0.00011** | 0.00007 | 0.00011 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `dbp_trend` | **0.00** | 5 | **0.00007** | 0.00003 | 0.00007 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `dbp_zscore` | **0.00** | 4 | **0.00004** | 0.00003 | 0.00005 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `sbp_value` | **0.00** | 4 | **0.00003** | 0.00002 | 0.00004 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `sbp_trend` | **0.00** | 3 | **0.00001** | 0.00001 | 0.00001 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `hr_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `sbp_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `dbp_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `rr_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `spo2_value` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `spo2_trend` | **0.00** | 1 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `spo2_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `temp_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `hours_since_last_vitals` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `patient_age` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `has_copd` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `has_post_op` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |
| `has_cardiac` | **0.00** | 0 | **0.00000** | 0.00000 | 0.00000 | NOT MEASURED | LightGBM split gain & TreeSHAP | Synthetic (50-patient calibrated cohort) |

---

## 2. Key Takeaways & Clinical Interpretation

1. **Personalized Z-Scores Outperform Static Cutoffs:**
   The four highest-gain features are `spo2_zscore` (124.89), `hr_zscore` (113.10), `sbp_zscore` (112.00), and `rr_zscore` (83.14). Raw threshold cutoffs (such as `rr_value` with gain 0.17 or `sbp_value` with gain 0.00) provide minimal split gain compared to relative vital deviations from the patient's own historical median.
2. **COPD Attributions are Calibrated:**
   For COPD patients who have chronic baseline respiratory elevation (RR 21–24), `rr_zscore` mean absolute SHAP is 0.11963 (vs 0.24665 for non-COPD patients). Because the patient's baseline is already adjusted, stable chronic high breathing rate does not trigger artificial risk spikes.
3. **Cohort Metadata:**
   - 50 patients total (373 evaluation rows).
   - 7 COPD-tagged patients (59 rows).
   - 43 Other patients (314 rows).

---

## 3. How to Reproduce

```bash
python scripts/compute_feature_importance.py
```
