"""
WardPulse evaluation dataset replay and downsampling module (P7).

Handles loading patient vitals from PhysioNet/CinC Challenge 2019 (.psv) files
and downsampling hourly ICU data to realistic 4-6 hour ward observation cadence.
Provides synthetic fallback case generation when raw data is not present.
"""

from __future__ import annotations

import glob
import math
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from shared.schemas import Condition, Consciousness, Patient, Source, VitalsReading


@dataclass
class ReplayCase:
    patient: Patient
    readings: List[VitalsReading] = field(default_factory=list)
    event_time: Optional[datetime] = None


def _parse_float(val: str) -> Optional[float]:
    """Parse float, converting 'NaN', empty string, or invalid text to None."""
    if not val:
        return None
    val_clean = val.strip()
    if val_clean in ("", "NaN", "nan", "None", "null"):
        return None
    try:
        f = float(val_clean)
        return None if math.isnan(f) else f
    except ValueError:
        return None


def parse_psv_patient(
    filepath: str | Path,
    patient_id: int,
    base_time: datetime = datetime(2026, 10, 1, 0, 0),
) -> tuple[Patient, list[dict], Optional[datetime]]:
    """Parse a single PhysioNet 2019 Challenge .psv file.
    
    Header format:
    HR|O2Sat|Temp|SBP|MAP|DBP|Resp|...|Age|Gender|...|ICULOS|SepsisLabel
    """
    rows = []
    age = 65
    event_time: Optional[datetime] = None

    with open(filepath, "r", encoding="utf-8") as f:
        header_line = f.readline().strip()
        headers = [h.strip() for h in header_line.split("|")]
        col_idx = {h: i for i, h in enumerate(headers)}

        hour_count = 0
        for line in f:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split("|")]
            hour_count += 1
            timestamp = base_time + timedelta(hours=hour_count)

            hr = _parse_float(parts[col_idx["HR"]]) if "HR" in col_idx else None
            sbp = _parse_float(parts[col_idx["SBP"]]) if "SBP" in col_idx else None
            dbp = _parse_float(parts[col_idx["DBP"]]) if "DBP" in col_idx else None
            rr = _parse_float(parts[col_idx["Resp"]]) if "Resp" in col_idx else None
            spo2 = _parse_float(parts[col_idx["O2Sat"]]) if "O2Sat" in col_idx else None
            temp = _parse_float(parts[col_idx["Temp"]]) if "Temp" in col_idx else None

            # Sanitize unphysical sensor artifacts to None matching VitalsBase schema bounds
            if hr is not None and not (0 <= hr <= 300):
                hr = None
            if sbp is not None and not (0 <= sbp <= 300):
                sbp = None
            if dbp is not None and not (0 <= dbp <= 200):
                dbp = None
            if sbp is not None and dbp is not None and sbp < dbp:
                sbp, dbp = None, None
            if rr is not None and not (0 <= rr <= 80):
                rr = None
            if spo2 is not None and not (0 <= spo2 <= 100):
                spo2 = None
            if temp is not None and not (25.0 <= temp <= 45.0):
                temp = None

            # Age
            if "Age" in col_idx:
                raw_age = _parse_float(parts[col_idx["Age"]])
                if raw_age is not None and not math.isnan(raw_age):
                    age = max(0, min(120, int(round(raw_age))))

            # SepsisLabel: in PhysioNet Challenge 2019, SepsisLabel is 1 starting 6 hours before
            # the clinical onset time t_sepsis. Thus clinical event_time = timestamp + 6h.
            if "SepsisLabel" in col_idx:
                label_val = _parse_float(parts[col_idx["SepsisLabel"]])
                if label_val is not None and int(label_val) == 1 and event_time is None:
                    event_time = timestamp + timedelta(hours=6)

            rows.append({
                "timestamp": timestamp,
                "hr": hr,
                "sbp": sbp,
                "dbp": dbp,
                "rr": rr,
                "spo2": spo2,
                "temp": temp,
            })

    patient = Patient(
        id=patient_id,
        bed=patient_id % 20 + 1,
        age=max(18, min(100, age)),
        conditions=[],
        admitted_at=base_time,
        display_name=f"Patient {patient_id}",
    )

    return patient, rows, event_time


def downsample_readings(
    hourly_rows: list[dict],
    patient_id: int,
    sampling_interval_hours: float = 4.0,
    seed: int = 42,
) -> List[VitalsReading]:
    """Downsample hourly ICU records to ward cadence (4 to 6 hours with jitter).
    
    Ensures missing values remain None, applies realistic gaps, and respects bounds.
    """
    if not hourly_rows:
        return []

    rng = random.Random(seed + patient_id)
    readings: List[VitalsReading] = []
    
    idx = 0
    reading_id = patient_id * 1000 + 1

    while idx < len(hourly_rows):
        row = hourly_rows[idx]

        # Check if row has at least one measured vital
        vitals_dict = {k: row[k] for k in ("hr", "sbp", "dbp", "rr", "spo2", "temp") if row[k] is not None}
        
        # If hourly row was completely empty, look forward 1-2 hours to find readings
        if not vitals_dict and idx + 1 < len(hourly_rows):
            idx += 1
            row = hourly_rows[idx]
            vitals_dict = {k: row[k] for k in ("hr", "sbp", "dbp", "rr", "spo2", "temp") if row[k] is not None}

        if vitals_dict:
            # SBP >= DBP validation
            sbp = row["sbp"]
            dbp = row["dbp"]
            if sbp is not None and dbp is not None and sbp < dbp:
                sbp = dbp + 10.0

            reading = VitalsReading(
                id=reading_id,
                patient_id=patient_id,
                timestamp=row["timestamp"],
                source=Source.REPLAY,
                hr=row["hr"],
                sbp=sbp,
                dbp=dbp,
                rr=row["rr"],
                spo2=row["spo2"],
                temp=row["temp"],
                on_oxygen=False,
                consciousness=Consciousness.ALERT,
            )
            readings.append(reading)
            reading_id += 1

        # Advance by sampling interval with jitter (e.g. 4 to 6 hours)
        step = int(round(rng.uniform(sampling_interval_hours, sampling_interval_hours + 2.0)))
        idx += max(1, step)

    return readings


def load_dataset(
    path: str | Path,
    sampling_interval_hours: float = 4.0,
    max_cases: Optional[int] = None,
) -> list[ReplayCase]:
    """Load and downsample patient cases from PhysioNet challenge directory.
    
    If path contains .psv files, parses them. If directory is empty,
    falls back to generating synthetic ward cases.
    """
    path_obj = Path(path)
    psv_files = list(path_obj.glob("*.psv")) if path_obj.exists() else []

    if not psv_files and path_obj.is_file() and str(path_obj).endswith(".psv"):
        psv_files = [path_obj]

    if not psv_files:
        # Check subdirectories
        psv_files = list(path_obj.glob("**/*.psv")) if path_obj.exists() else []

    if not psv_files:
        n_synth = min(50, max_cases) if max_cases is not None else 50
        return generate_synthetic_cases(n_cases=n_synth)

    # Deterministic alphabetical sort across platforms
    psv_files = sorted(psv_files, key=lambda p: p.name)

    if max_cases is not None:
        psv_files = psv_files[:max_cases]

    cases: list[ReplayCase] = []
    for pid, psv_file in enumerate(psv_files, start=1):
        patient, hourly_rows, event_time = parse_psv_patient(psv_file, pid)
        readings = downsample_readings(hourly_rows, pid, sampling_interval_hours, seed=42)
        if readings:
            cases.append(ReplayCase(patient=patient, readings=readings, event_time=event_time))

    return cases


def generate_synthetic_cases(n_cases: int = 50, seed: int = 42) -> list[ReplayCase]:
    """Generate realistic synthetic evaluation cases with known deterioration events.
    
    Mix:
      - 35% deteriorating cases (sepsis onset with tachycardia, tachypnea, hypotension, fever)
      - 45% stable recovery cases
      - 20% chronic abnormal stable cases (COPD with elevated baseline RR, cardiac)
    """
    rng = random.Random(seed)
    cases: list[ReplayCase] = []
    base_time = datetime(2026, 10, 1, 6, 0)

    for i in range(1, n_cases + 1):
        case_type = "deteriorating" if i % 3 == 0 else ("chronic" if i % 5 == 0 else "stable")
        age = rng.randint(40, 88)
        conds = [Condition.COPD] if case_type == "chronic" else []

        patient = Patient(
            id=i,
            bed=(i - 1) % 20 + 1,
            age=age,
            conditions=conds,
            admitted_at=base_time,
            display_name=f"Synthetic Patient {i}",
        )

        readings: list[VitalsReading] = []
        event_time: Optional[datetime] = None
        
        # 36 hours total observation time
        # Gaps between 4 and 6 hours
        current_time = base_time
        curr_hr = 72.0 + rng.uniform(-6, 6)
        curr_sbp = 122.0 + rng.uniform(-8, 8)
        curr_dbp = 76.0 + rng.uniform(-6, 6)
        curr_rr = 21.0 if case_type == "chronic" else (15.0 + rng.uniform(-2, 2))
        curr_spo2 = 91.0 if case_type == "chronic" else 98.0
        curr_temp = 36.7

        # Deterioration begins around hour 14-18, clinical event/shock occurs 8-10h later
        deterioration_start_hour = rng.randint(14, 18) if case_type == "deteriorating" else 999
        event_hour = deterioration_start_hour + rng.randint(8, 10) if case_type == "deteriorating" else None
        event_time = base_time + timedelta(hours=event_hour) if event_hour else None

        reading_id = i * 1000 + 1
        hour = 0
        while hour < 40:
            current_time = base_time + timedelta(hours=hour)

            if case_type == "deteriorating" and hour >= deterioration_start_hour:
                # Progression of sepsis / clinical deterioration
                curr_hr = min(145.0, curr_hr + rng.uniform(5, 9))
                curr_rr = min(32.0, curr_rr + rng.uniform(2, 4))
                curr_sbp = max(75.0, curr_sbp - rng.uniform(6, 10))
                curr_dbp = max(48.0, curr_dbp - rng.uniform(4, 7))
                curr_spo2 = max(87.0, curr_spo2 - rng.uniform(1.2, 2.5))
                curr_temp = min(39.2, curr_temp + rng.uniform(0.3, 0.5))
            else:
                # Normal minor physiological fluctuation
                curr_hr = max(55.0, min(100.0, curr_hr + rng.uniform(-3, 3)))
                curr_sbp = max(95.0, min(145.0, curr_sbp + rng.uniform(-4, 4)))
                curr_dbp = max(60.0, min(90.0, curr_dbp + rng.uniform(-3, 3)))
                if case_type != "chronic":
                    curr_rr = max(12.0, min(20.0, curr_rr + rng.uniform(-1, 1)))
                    curr_spo2 = max(94.0, min(100.0, curr_spo2 + rng.uniform(-1, 1)))
                else:
                    curr_rr = max(20.0, min(24.0, curr_rr + rng.uniform(-0.5, 0.5)))
                    curr_spo2 = max(89.0, min(92.0, curr_spo2 + rng.uniform(-0.5, 0.5)))
                curr_temp = round(36.5 + rng.uniform(-0.3, 0.3), 1)

            # Random 10% omission of single vital
            r_sbp = None if rng.random() < 0.1 else round(curr_sbp, 1)
            r_dbp = None if r_sbp is None or rng.random() < 0.1 else round(curr_dbp, 1)

            readings.append(
                VitalsReading(
                    id=reading_id,
                    patient_id=i,
                    timestamp=current_time,
                    source=Source.REPLAY,
                    hr=round(curr_hr, 1),
                    sbp=r_sbp,
                    dbp=r_dbp,
                    rr=round(curr_rr, 1),
                    spo2=round(curr_spo2, 1),
                    temp=round(curr_temp, 1),
                    on_oxygen=case_type == "chronic",
                    consciousness=Consciousness.ALERT if (case_type != "deteriorating" or hour < deterioration_start_hour + 6) else Consciousness.CONFUSION,
                )
            )
            reading_id += 1
            hour += rng.randint(4, 6)

        cases.append(ReplayCase(patient=patient, readings=readings, event_time=event_time))

    return cases
