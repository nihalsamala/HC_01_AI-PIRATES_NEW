"""
Ward simulator and patient builder.
"""

from datetime import datetime, timedelta
import random
from typing import List, Tuple

from shared.schemas import Consciousness, Patient, Source, VitalsReading
from simulator.clock import Simulator
from simulator.scenarios import (
    BED_CONFIGS,
    DELIBERATELY_MISSED_READINGS,
    SIM_START,
)


def build_ward(seed: int = 42) -> Tuple[List[Patient], List[VitalsReading]]:
    """Build simulated ward patients and prior vitals history.
    
    Creates 20 patients (beds 1 to 20) with anonymous display names and varied ages,
    plus approximately 24 hours of prior vitals history ending at SIM_START.
    Uses random.Random(seed) exclusively to guarantee identical results for the same seed.
    """
    rng = random.Random(seed)

    # 1. Build 20 patients
    patients: List[Patient] = []
    for bed in range(1, 21):
        cfg = BED_CONFIGS[bed]
        admit_offset_hours = 24.0 + (bed * 1.5)
        patients.append(
            Patient(
                id=bed,
                bed=bed,
                age=cfg.age,
                conditions=cfg.conditions,
                admitted_at=SIM_START - timedelta(hours=admit_offset_hours),
                display_name=f"Bed {bed}",
            )
        )

    # 2. Build 24 hours of history ending at SIM_START
    readings: List[VitalsReading] = []
    reading_id = 1

    # Standard scheduled slots (hours before SIM_START)
    # Most beds measured roughly every 4 to 6 hours
    nominal_offsets = [24.0, 19.5, 15.0, 10.5, 6.0, 1.0]

    for bed in range(1, 21):
        cfg = BED_CONFIGS[bed]

        # Bed-specific custom history:
        if bed == 3:
            # Bed 3: COPD chronic, RR 21 to 23, SpO2 90 to 92 for whole history
            rr_pattern = [21.0, 22.0, 22.0, 23.0, 22.0, 22.0]
            spo2_pattern = [91.0, 91.0, 90.0, 92.0, 91.0, 91.0]
            for idx, offset in enumerate(nominal_offsets):
                t_reading = SIM_START - timedelta(hours=offset)
                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=bed,
                        timestamp=t_reading,
                        source=Source.SIM,
                        hr=82.0 + (idx % 3),
                        sbp=126.0 + (idx % 3),
                        dbp=80.0 + (idx % 2),
                        rr=rr_pattern[idx],
                        spo2=spo2_pattern[idx],
                        temp=36.8,
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )
                reading_id += 1
            continue

        if bed == 7:
            # Bed 7: Post-op deterioration RR 14 -> 14 -> 15 -> 17, pulse rising gently
            rr_pattern = [14.0, 14.0, 15.0, 17.0, 17.0]
            hr_pattern = [72.0, 76.0, 82.0, 88.0, 92.0]
            post_op_offsets = [19.5, 15.0, 10.5, 5.5, 1.0]
            for idx, offset in enumerate(post_op_offsets):
                t_reading = SIM_START - timedelta(hours=offset)
                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=bed,
                        timestamp=t_reading,
                        source=Source.SIM,
                        hr=hr_pattern[idx],
                        sbp=122.0 - (idx * 2),
                        dbp=78.0 - (idx * 1.5),
                        rr=rr_pattern[idx],
                        spo2=98.0 - (idx * 0.5),
                        temp=36.8 + (idx * 0.1),
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )
                reading_id += 1
            continue

        if bed == 4:
            # Bed 4: Falling SBP earlier (128 -> 112); last BP at SIM_START - 4h (7h old at +3h);
            # other vitals retaken at SIM_START - 1h.
            bed4_schedule = [
                (24.0, 128.0, 80.0, 74.0, 15.0, 98.0, 36.6),
                (19.0, 124.0, 78.0, 76.0, 15.0, 97.0, 36.6),
                (14.0, 120.0, 76.0, 78.0, 16.0, 97.0, 36.7),
                (9.0, 116.0, 74.0, 80.0, 16.0, 97.0, 36.7),
                (4.0, 112.0, 70.0, 80.0, 16.0, 97.0, 36.7),   # Last BP taken here (02:00:00)
                (1.0, None, None, 82.0, 16.0, 97.0, 36.8),     # BP omitted at 05:00:00
            ]
            for offset, sbp, dbp, hr, rr, spo2, temp in bed4_schedule:
                t_reading = SIM_START - timedelta(hours=offset)
                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=bed,
                        timestamp=t_reading,
                        source=Source.SIM,
                        hr=hr,
                        sbp=sbp,
                        dbp=dbp,
                        rr=rr,
                        spo2=spo2,
                        temp=temp,
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )
                reading_id += 1
            continue

        # General beds (1, 2, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
        for slot_idx, offset in enumerate(nominal_offsets):
            # Check for deliberate missed readings
            if bed == 8 and slot_idx == 2:
                continue  # Bed 8 missed slot 2 (-15h)
            if bed == 15 and slot_idx == 3:
                continue  # Bed 15 missed slot 3 (-10.5h)
            if bed == 19 and slot_idx == 4:
                continue  # Bed 19 missed slot 4 (-6h)

            jitter_minutes = rng.uniform(-15.0, 15.0)
            t_reading = SIM_START - timedelta(hours=offset, minutes=jitter_minutes)

            # Check for occasional single missing vital
            temp_val: float | None = round(cfg.base_temp + rng.uniform(-0.2, 0.2), 1)
            dbp_val: float | None = round(cfg.base_dbp + rng.uniform(-2, 2), 1)
            if bed == 2 and slot_idx == 3:
                temp_val = None
            if bed == 11 and slot_idx == 4:
                temp_val = None
            if bed == 16 and slot_idx == 1:
                dbp_val = None

            if cfg.role == "copd_chronic":
                rr_val = round(rng.uniform(21.0, 23.0), 1)
                spo2_val = round(rng.uniform(90.0, 92.0), 1)
                hr_val = round(cfg.base_hr + rng.uniform(-2, 2), 1)
                sbp_val = round(cfg.base_sbp + rng.uniform(-3, 3), 1)
            elif cfg.role == "cardiac_chronic":
                rr_val = round(cfg.base_rr + rng.uniform(-1, 1), 1)
                spo2_val = round(cfg.base_spo2 + rng.uniform(-1, 1), 1)
                hr_val = round(cfg.base_hr + rng.uniform(-2, 3), 1)
                sbp_val = round(cfg.base_sbp + rng.uniform(-3, 3), 1)
            else:
                rr_val = round(cfg.base_rr + rng.uniform(-1, 1), 1)
                spo2_val = round(min(100.0, cfg.base_spo2 + rng.uniform(-1, 1)), 1)
                hr_val = round(cfg.base_hr + rng.uniform(-3, 3), 1)
                sbp_val = round(cfg.base_sbp + rng.uniform(-3, 3), 1)

            readings.append(
                VitalsReading(
                    id=reading_id,
                    patient_id=bed,
                    timestamp=t_reading,
                    source=Source.SIM,
                    hr=hr_val,
                    sbp=sbp_val,
                    dbp=dbp_val,
                    rr=rr_val,
                    spo2=spo2_val,
                    temp=temp_val,
                    on_oxygen=False,
                    consciousness=Consciousness.ALERT,
                )
            )
            reading_id += 1

    # Sort all readings chronologically
    readings.sort(key=lambda r: r.timestamp)
    return (patients, readings)


# Re-export Simulator for backwards and contract compatibility
__all__ = ["build_ward", "Simulator", "DELIBERATELY_MISSED_READINGS", "SIM_START"]
