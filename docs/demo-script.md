# WardPulse Demonstration Script

This document scripts the live demonstration of WardPulse for hackathon judges and clinical evaluators.
It shows how WardPulse prevents alarm fatigue and allocates nurse attention across a 20-bed hospital ward.

---

## Simulation Setup

- **Simulation Start Time (`SIM_START`)**: `2026-10-20 06:00:00`
- **Ward Configuration**: 20 general ward beds with varied ages and conditions (COPD, post-op, cardiac, general recovery).
- **History**: 24 hours of prior vitals recorded at realistic 4–6 hour intervals with minor time jitter and measurement noise.
- **Attention Budget**: $K = 2$ active cards maximum on screen. Unequivocal crash cases trigger **Crash Bypass**.

---

## Scripted Stories and Timeline

### Story 1: Same Number, Different Patients
- **Simulation Time**: `2026-10-20 07:00:00` (`SIM_START + 1h`)
- **Clinical Scenario**:
  - **Bed 3 (COPD)**: Has a chronic respiratory rate of 21–23 breaths/min and $\text{SpO}_2$ 90–92% across the entire 24-hour history.
  - **Bed 7 (Post-op)**: Underwent surgery 20 hours ago. Her respiratory rate was previously normal and steady (14, 14, 15, 17 breaths/min) with a rising pulse (72 $\to$ 92 bpm). At 07:00, her RR reaches **22 breaths/min** and pulse reaches **98 bpm**.
  - **The Dilemma**: Both patients now have the exact same respiratory rate ($RR = 22$).
- **What the Audience Sees**:
  - **Naive AI (NEWS2 Mode)**:
    - Fixed thresholds flag Bed 3 with high scores ($\text{SpO}_2 \le 91\%$ scores 3 points, $RR \ge 21$ scores 2 points).
    - Flags Bed 7, Bed 3, Bed 5, Bed 9, Bed 14, Bed 18 simultaneously (6+ loud alarms).
  - **WardPulse Mode**:
    - Evaluates each patient against their **personal baseline** and condition prior.
    - **Bed 3**: Identified as stable chronic baseline $\to$ **No card**.
    - **Bed 7**: Identified as acute post-op deterioration $\to$ **Active card** surfaced: `"Recount breathing rate: Bed 7"` / `"Page the on-duty doctor: Bed 7"`.
  - **Key Takeaway**: WardPulse treats patients, not isolated numbers.

---

### Story 2: Stale BP vs. False Alarm
- **Simulation Time**: `2026-10-20 09:00:00` (`SIM_START + 3h`)
- **Clinical Scenario**:
  - **Bed 4**: Had borderline and gently falling systolic blood pressure earlier (128 down to 112 mmHg).
  - Last manual BP was taken at `02:00:00` (`SIM_START - 4h`).
  - At `05:00:00` (`SIM_START - 1h`), other vitals were retaken, but the blood pressure cuff was omitted.
  - At `09:00:00`, Bed 4's blood pressure measurement is now **7 hours old** ($> 1.5\times$ the recommended due interval).
- **What the Audience Sees**:
  - **Naive / Poorly Designed AI**: Predicts "High Risk of Shock" because the last recorded BP was low.
  - **WardPulse Mode**:
    - Disentangles **risk** from **freshness**.
    - Because the vital is stale rather than acutely plummeting, WardPulse emits:
      `"Repeat manual BP: Bed 4"` with reason `"BP not taken for 7h; prior SBP 112"`.
    - It instructs the nurse to verify the measurement before escalating to a doctor.
    - **Slots Occupied**: Bed 7 and Bed 4 now fill the $K = 2$ active slots.
  - **Key Takeaway**: Never confuse outdated data with an acute emergency.

---

### Story 3: Crash Bypass
- **Simulation Time**: `2026-10-20 11:00:00` (`SIM_START + 5h`)
- **Clinical Scenario**:
  - **Bed 12**: A patient who has been completely stable all day suddenly exhibits severe septic shock vitals:
    - Systolic BP: **78 mmHg**
    - Heart Rate: **135 bpm**
    - $\text{SpO}_2$: **86%**
    - Respiratory Rate: **28 breaths/min**
    - Consciousness: **Confusion (C)**
  - **The Dilemma**: Beds 7 and 4 already occupy the $K=2$ available slots on the nurse's screen. In a naive queue, Bed 12 would be hidden in the backlog.
- **What the Audience Sees**:
  - WardPulse's **Hard Safety Layer** evaluates absolute red-line criteria.
  - Bed 12 unequivocally trips `is_crash(...) == True`.
  - **Crash Bypass Triggered**:
    - Bed 12 immediately surfaces in a high-priority red **EMERGENCY BANNER** at the very top of the console.
    - Beds 7 and 4 remain in their active attention slots.
  - **Key Takeaway**: Safe attention allocation budgets must always have a hard-coded bypass for unequivocal clinical crashes.

---

## Demonstrating Naive Mode vs. WardPulse Mode (The Toggle Demo)

During the presentation, toggle between **WardPulse Mode** and **Naive NEWS2 Mode**:

| Feature | Naive AI (NEWS2) | WardPulse |
|---|---|---|
| **Attention Budget** | None (unbounded alerts) | Strict $K = 2$ active cards + Emergency |
| **Active Cards on Screen** | 6 to 10 simultaneous alerts | Exactly 2 active cards + Crash Banner |
| **Bed 3 (Stable COPD)** | Red alert (Score $\ge 5$) | Quiet / Watch (Personal baseline recognized) |
| **Bed 4 (Stale BP)** | Alarms or misses staleness | Actionable card: `"Repeat manual BP"` |
| **Bed 12 (Crash)** | Just another card in a long list | Instant top-of-screen Emergency Banner |
| **Nurse Cognitive Load** | Extreme alarm fatigue | Clear, prioritized, 15-minute action plan |
