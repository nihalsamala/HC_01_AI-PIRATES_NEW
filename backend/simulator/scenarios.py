"""
WardPulse Simulator Scenarios and Scripted Timeline.

Scripted Timeline:
==================
SIM_START = 2026-10-20 06:00:00 (Fixed simulation baseline)

- SIM_START - 24h to SIM_START (Prior History):
  * 20 patients (Beds 1 to 20) with anonymous labels "Bed 1" .. "Bed 20".
  * Most beds get vitals every 4 to 6 hours with small jitter and realistic noise.
  * Deliberately missed scheduled readings:
    - Bed 8: Missed at ~15:00 on Day -1
    - Bed 15: Missed at ~19:30 on Day -1
    - Bed 19: Missed at ~00:00 on Day 0
  * Bed 3 (COPD): Chronic stable respiratory rate between 21 and 23 bpm,
    SpO2 ~90-92% across all 24 hours. Under NEWS2, this flags 4-5 points.
    Under WardPulse, personal baseline identifies it as normal.
  * Bed 7 (Post-op): Gradual respiratory deterioration in history:
    RR 14 -> 14 -> 15 -> 17, with heart rate rising gently (72 -> 76 -> 82 -> 88 bpm).
  * Bed 4: Falling/borderline SBP in history (128 down to 112 mmHg).
    Last blood pressure was taken at SIM_START - 4h (02:00:00).
    At SIM_START - 1h (05:00:00), other vitals (HR, RR, SpO2, temp) were retaken,
    but BP was omitted.
  * Beds 5, 9, 14, 18: Four additional chronic-abnormal patients (COPD and Cardiac)
    whose vitals are abnormal on fixed NEWS2 scales but completely stable for their baseline.
  * Bed 12: Completely normal, stable vitals throughout history.

- SIM_START + 1h (2026-10-20 07:00:00) - Story 1: Same Number, Different Patients
  * Bed 7 records RR=22 bpm, HR=98 bpm, SpO2=95%.
  * Both Bed 3 and Bed 7 have latest RR=22 bpm.
  * Audience sees:
    - WardPulse: Bed 7 gets an ACTIVE action card (page doctor / recount respiratory rate);
      Bed 3 gets NO card (RR 22 is normal for their COPD baseline).
    - Naive NEWS2: flags both Bed 3 and Bed 7 with high alert scores, plus Beds 5, 9, 14, 18.

- SIM_START + 3h (2026-10-20 09:00:00) - Story 2: Stale BP vs False Alarm
  * Bed 4 has not had blood pressure taken since 02:00:00 (now 7 hours old).
  * Other vitals are recent (~1h old).
  * Audience sees:
    - WardPulse: Surfaces "Repeat manual BP: Bed 4", NOT "page doctor".
      Distinguishes stale data from clinical emergency.
    - Beds 7 and 4 now fill the K=2 active card slots.

- SIM_START + 5h (2026-10-20 11:00:00) - Story 3: Crash Bypass
  * Bed 12 suddenly crashes: SBP=78 mmHg, HR=135 bpm, SpO2=86%, RR=28 bpm, confusion.
  * Beds 7 and 4 already occupy the K=2 active slots.
  * Audience sees:
    - Normal cards would be queued, but Bed 12 triggers unequivocal CRASH BYPASS.
    - An EMERGENCY banner for Bed 12 appears immediately at the top of the nurse console,
      while Beds 7 and 4 remain active in their allocated slots.
"""

from datetime import datetime, timedelta
from typing import Dict, List, NamedTuple, Optional

from shared.schemas import Condition, Consciousness


SIM_START = datetime(2026, 10, 20, 6, 0, 0)


class BedConfig(NamedTuple):
    bed: int
    age: int
    conditions: List[Condition]
    role: str
    base_hr: float
    base_sbp: float
    base_dbp: float
    base_rr: float
    base_spo2: float
    base_temp: float


# Definitions for all 20 ward beds
BED_CONFIGS: Dict[int, BedConfig] = {
    1: BedConfig(1, 48, [], "normal", 72, 120, 78, 15, 98, 36.6),
    2: BedConfig(2, 65, [], "normal", 74, 122, 76, 16, 97, 36.7),
    3: BedConfig(3, 68, [Condition.COPD], "copd_chronic", 82, 126, 80, 22, 91, 36.8),
    4: BedConfig(4, 62, [], "stale_bp", 80, 112, 70, 16, 97, 36.7),
    5: BedConfig(5, 74, [Condition.COPD], "copd_chronic", 80, 124, 78, 22, 91, 36.7),
    6: BedConfig(6, 39, [], "normal", 68, 118, 74, 14, 99, 36.5),
    7: BedConfig(7, 54, [Condition.POST_OP], "post_op_deterioration", 72, 122, 78, 14, 98, 36.8),
    8: BedConfig(8, 59, [], "normal_missed_slot", 70, 124, 78, 15, 98, 36.6),
    9: BedConfig(9, 71, [Condition.CARDIAC], "cardiac_chronic", 100, 150, 92, 18, 96, 36.8),
    10: BedConfig(10, 42, [], "normal", 76, 118, 76, 14, 98, 36.6),
    11: BedConfig(11, 57, [], "normal", 72, 120, 78, 15, 97, 36.7),
    12: BedConfig(12, 70, [], "crash_patient", 75, 124, 78, 15, 98, 36.6),
    13: BedConfig(13, 31, [], "normal", 66, 116, 72, 13, 99, 36.5),
    14: BedConfig(14, 67, [Condition.COPD], "copd_chronic", 82, 128, 80, 21, 91, 36.8),
    15: BedConfig(15, 81, [], "normal_missed_slot", 74, 122, 76, 16, 96, 36.6),
    16: BedConfig(16, 52, [], "normal", 70, 120, 76, 15, 98, 36.6),
    17: BedConfig(17, 46, [Condition.POST_OP], "normal_post_op", 78, 126, 80, 16, 97, 36.9),
    18: BedConfig(18, 76, [Condition.CARDIAC], "cardiac_chronic", 94, 154, 92, 17, 96, 36.7),
    19: BedConfig(19, 63, [], "normal_missed_slot", 72, 122, 78, 15, 97, 36.6),
    20: BedConfig(20, 58, [], "normal", 75, 120, 76, 16, 98, 36.6),
}


# Deliberately missed reading slots across the 24-hour history
DELIBERATELY_MISSED_READINGS = [
    {"bed": 8, "scheduled_time": SIM_START - timedelta(hours=15), "reason": "Ward emergency in neighboring bay"},
    {"bed": 15, "scheduled_time": SIM_START - timedelta(hours=10, minutes=30), "reason": "Patient away in radiology"},
    {"bed": 19, "scheduled_time": SIM_START - timedelta(hours=6), "reason": "Staffing shortage during midnight shift change"},
]
