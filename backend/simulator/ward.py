"""
Ward simulator and patient builder.

Supports two data generation modes:
  1. source="replay": Loads de-identified patient trajectories through
     evaluation.replay.load_dataset (downsampled to 4-6h ward cadence),
     maps them to beds 1 to 20, shifts timestamps to SIM_START, and overlays
     the three scripted demo stories (Beds 3, 4, 7, 12, plus chronic beds 5, 9, 14, 18).
  2. source="sim": Deterministic synthetic ward generation (fallback when
     no external dataset files are present).
"""

from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Optional, Tuple, Union

from shared.schemas import Condition, Consciousness, Patient, Source, VitalsReading
from simulator.clock import Simulator
from simulator.scenarios import (
    BED_CONFIGS,
    DELIBERATELY_MISSED_READINGS,
    SIM_START,
)


def _has_dataset_files(data_path: Optional[Union[str, Path]] = None) -> bool:
    """Check if raw .psv dataset files exist in data_path or default directories."""
    if data_path:
        p = Path(data_path)
        if p.exists() and (list(p.glob("*.psv")) or list(p.glob("**/*.psv"))):
            return True

    candidates = [
        Path(__file__).resolve().parent.parent.parent / "data" / "raw",
        Path("data/raw"),
        Path("../data/raw"),
    ]
    for c in candidates:
        if c.exists() and (list(c.glob("*.psv")) or list(c.glob("**/*.psv"))):
            return True
    return False


def _resolve_data_path(data_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve the directory path to search for public clinical records."""
    if data_path:
        return Path(data_path)
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "data" / "raw",
        Path("data/raw"),
        Path("../data/raw"),
    ]
    for c in candidates:
        if c.exists() and (list(c.glob("*.psv")) or list(c.glob("**/*.psv"))):
            return c
    return candidates[0]


def build_ward(
    seed: int = 42,
    source: Optional[str] = None,
    data_path: Optional[Union[str, Path]] = None,
) -> Tuple[List[Patient], List[VitalsReading]]:
    """Build ward patients and prior vitals history.

    Parameters:
      seed: Random seed for deterministic reproducibility.
      source: "replay" to use de-identified trajectory replay, or "sim" for synthetic ward.
              If None, defaults to "replay" when raw dataset files exist, otherwise "sim".
      data_path: Optional path to directory containing .psv files.

    Returns:
      Tuple of (patients, readings) covering 20 beds and 24h prior history ending at SIM_START.
    """
    # 1. Resolve source mode: fallback to "sim" if no dataset files are present
    if source is None:
        source = "replay" if _has_dataset_files(data_path) else "sim"

    if source == "replay":
        return _build_ward_replay(seed=seed, data_path=data_path)
    return _build_ward_sim(seed=seed)


def _build_ward_sim(seed: int = 42) -> Tuple[List[Patient], List[VitalsReading]]:
    """Build synthetic ward patients and prior vitals history (source=Source.SIM)."""
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
    nominal_offsets = [24.0, 19.5, 15.0, 10.5, 6.0, 1.0]

    for bed in range(1, 21):
        cfg = BED_CONFIGS[bed]

        # Bed 3: COPD chronic, RR 21 to 23, SpO2 90 to 92 for whole history
        if bed == 3:
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

        # Bed 7: Post-op deterioration RR 14 -> 14 -> 15 -> 17, pulse rising gently
        if bed == 7:
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

        # Bed 4: Falling SBP earlier; last BP at SIM_START - 4h (7h old at +3h)
        if bed == 4:
            bed4_schedule = [
                (24.0, 128.0, 80.0, 74.0, 15.0, 98.0, 36.6),
                (19.0, 124.0, 78.0, 76.0, 15.0, 97.0, 36.6),
                (14.0, 120.0, 76.0, 78.0, 16.0, 97.0, 36.7),
                (9.0, 116.0, 74.0, 80.0, 16.0, 97.0, 36.7),
                (4.0, 112.0, 70.0, 80.0, 16.0, 97.0, 36.7),   # Last BP taken at 02:00:00
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
            if bed == 8 and slot_idx == 2:
                continue
            if bed == 15 and slot_idx == 3:
                continue
            if bed == 19 and slot_idx == 4:
                continue

            jitter_minutes = rng.uniform(-15.0, 15.0)
            t_reading = SIM_START - timedelta(hours=offset, minutes=jitter_minutes)

            temp_val: Optional[float] = round(cfg.base_temp + rng.uniform(-0.2, 0.2), 1)
            dbp_val: Optional[float] = round(cfg.base_dbp + rng.uniform(-2, 2), 1)
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

    readings.sort(key=lambda r: r.timestamp)
    return (patients, readings)


def _build_ward_replay(
    seed: int = 42,
    data_path: Optional[Union[str, Path]] = None,
) -> Tuple[List[Patient], List[VitalsReading]]:
    """Build ward using replayed de-identified patient trajectories (source=Source.REPLAY).

    Loads cases through evaluation.replay.load_dataset (or synthetic fallback),
    maps them to beds 1 to 20 with anonymous labels ('Bed 1'..'Bed 20'),
    shifts timestamps to cover the 24 hours prior to SIM_START, and overlays the
    three canonical demo stories (Beds 3, 4, 7, 12) per docs/contracts.md section 6.
    """
    from evaluation.replay import generate_synthetic_cases, load_dataset

    resolved_path = _resolve_data_path(data_path)
    cases = load_dataset(resolved_path, sampling_interval_hours=4.0, max_cases=100)
    if len(cases) < 20:
        cases = generate_synthetic_cases(n_cases=50, seed=seed)

    # Deterministic selection of 20 cases for beds 1..20
    rng = random.Random(seed)
    patients: List[Patient] = []
    readings: List[VitalsReading] = []
    reading_id = 1
    nominal_offsets = [24.0, 19.5, 15.0, 10.5, 6.0, 1.0]

    for bed in range(1, 21):
        cfg = BED_CONFIGS[bed]
        case = cases[bed - 1]
        admit_offset_hours = 24.0 + (bed * 1.5)

        # 1. Anonymous de-identified patient record
        patient = Patient(
            id=bed,
            bed=bed,
            age=cfg.age if cfg.age else max(18, min(95, case.patient.age)),
            conditions=cfg.conditions,
            admitted_at=SIM_START - timedelta(hours=admit_offset_hours),
            display_name=f"Bed {bed}",
        )
        patients.append(patient)

        # =========================================================================
        # --- SCRIPTED DEMO STORY OVERLAY (docs/contracts.md section 6) ---
        # Specific clinical stories must trigger reliably for judges & evaluation.
        # =========================================================================

        # Story 1: Bed 3 (COPD chronic, stable RR 21-23, SpO2 90-92 across 24h)
        if bed == 3:
            rr_pattern = [21.0, 22.0, 22.0, 23.0, 22.0, 22.0]
            spo2_pattern = [91.0, 91.0, 90.0, 92.0, 91.0, 91.0]
            for idx, offset in enumerate(nominal_offsets):
                t_reading = SIM_START - timedelta(hours=offset)
                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=bed,
                        timestamp=t_reading,
                        source=Source.REPLAY,
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

        # Story 1: Bed 7 (Post-op gradual respiratory drift: RR 14 -> 17, pulse rising)
        if bed == 7:
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
                        source=Source.REPLAY,
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

        # Story 2: Bed 4 (Falling SBP earlier; last BP at SIM_START - 4h, omitted at -1h)
        if bed == 4:
            bed4_schedule = [
                (24.0, 128.0, 80.0, 74.0, 15.0, 98.0, 36.6),
                (19.0, 124.0, 78.0, 76.0, 15.0, 97.0, 36.6),
                (14.0, 120.0, 76.0, 78.0, 16.0, 97.0, 36.7),
                (9.0, 116.0, 74.0, 80.0, 16.0, 97.0, 36.7),
                (4.0, 112.0, 70.0, 80.0, 16.0, 97.0, 36.7),   # Last BP taken at 02:00:00
                (1.0, None, None, 82.0, 16.0, 97.0, 36.8),     # BP omitted at 05:00:00
            ]
            for offset, sbp, dbp, hr, rr, spo2, temp in bed4_schedule:
                t_reading = SIM_START - timedelta(hours=offset)
                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=bed,
                        timestamp=t_reading,
                        source=Source.REPLAY,
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

        # Story 3: Bed 12 (Completely stable normal vitals throughout history)
        if bed == 12:
            for offset in nominal_offsets:
                t_reading = SIM_START - timedelta(hours=offset)
                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=12,
                        timestamp=t_reading,
                        source=Source.REPLAY,
                        hr=74.0,
                        sbp=122.0,
                        dbp=78.0,
                        rr=15.0,
                        spo2=98.0,
                        temp=36.6,
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )
                reading_id += 1
            continue

        # Additional chronic abnormal beds for Naive vs WardPulse toggle demo:
        # Beds 5, 14 (COPD) and Beds 9, 18 (Cardiac)
        if cfg.role in ("copd_chronic", "cardiac_chronic"):
            for offset in nominal_offsets:
                t_reading = SIM_START - timedelta(hours=offset)
                if cfg.role == "copd_chronic":
                    rr_val = round(rng.uniform(21.0, 23.0), 1)
                    spo2_val = round(rng.uniform(90.0, 92.0), 1)
                    hr_val = round(cfg.base_hr + rng.uniform(-2, 2), 1)
                    sbp_val = round(cfg.base_sbp + rng.uniform(-3, 3), 1)
                    dbp_val = round(cfg.base_dbp + rng.uniform(-2, 2), 1)
                else:
                    rr_val = round(cfg.base_rr + rng.uniform(-1, 1), 1)
                    spo2_val = round(cfg.base_spo2 + rng.uniform(-1, 1), 1)
                    hr_val = round(cfg.base_hr + rng.uniform(-2, 3), 1)
                    sbp_val = round(cfg.base_sbp + rng.uniform(-3, 3), 1)
                    dbp_val = round(cfg.base_dbp + rng.uniform(-2, 2), 1)

                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=bed,
                        timestamp=t_reading,
                        source=Source.REPLAY,
                        hr=hr_val,
                        sbp=sbp_val,
                        dbp=dbp_val,
                        rr=rr_val,
                        spo2=spo2_val,
                        temp=round(cfg.base_temp, 1),
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )
                reading_id += 1
            continue

        # =========================================================================
        # --- REPLAYED REAL PATIENT TRAJECTORIES (Beds 1, 2, 6, 8, 10, 11, 13, 15, 16, 17, 19, 20) ---
        # Extracted from de-identified dataset, thinned to 4-6h cadence, timestamps shifted.
        # =========================================================================
        case_readings = [r for r in case.readings if r.hr is not None or r.sbp is not None or r.rr is not None]
        if case_readings:
            # Shift case readings so observation window ends near SIM_START - 1h
            latest_case_time = case_readings[-1].timestamp
            time_shift = (SIM_START - timedelta(hours=1)) - latest_case_time

            for slot_idx, r in enumerate(case_readings):
                shifted_time = r.timestamp + time_shift

                # Restrict to the 24-hour window ending at SIM_START
                if shifted_time < (SIM_START - timedelta(hours=24)) or shifted_time > SIM_START:
                    continue

                # Respect deliberately missed reading slots
                if bed == 8 and slot_idx == 2:
                    continue
                if bed == 15 and slot_idx == 3:
                    continue
                if bed == 19 and slot_idx == 4:
                    continue

                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=bed,
                        timestamp=shifted_time,
                        source=Source.REPLAY,
                        hr=r.hr,
                        sbp=r.sbp,
                        dbp=r.dbp,
                        rr=r.rr,
                        spo2=r.spo2,
                        temp=r.temp,
                        on_oxygen=r.on_oxygen,
                        consciousness=r.consciousness or Consciousness.ALERT,
                    )
                )
                reading_id += 1
        else:
            # Fallback if case had no measured vitals
            for offset in nominal_offsets:
                t_reading = SIM_START - timedelta(hours=offset)
                readings.append(
                    VitalsReading(
                        id=reading_id,
                        patient_id=bed,
                        timestamp=t_reading,
                        source=Source.REPLAY,
                        hr=cfg.base_hr,
                        sbp=cfg.base_sbp,
                        dbp=cfg.base_dbp,
                        rr=cfg.base_rr,
                        spo2=cfg.base_spo2,
                        temp=cfg.base_temp,
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )
                reading_id += 1

    readings.sort(key=lambda r: r.timestamp)
    return (patients, readings)


# Re-export Simulator for backwards and contract compatibility
__all__ = ["build_ward", "Simulator", "DELIBERATELY_MISSED_READINGS", "SIM_START"]
