"""
Ward simulation clock and event generator.
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional

from shared.schemas import Consciousness, Source, VitalsIn
from simulator.scenarios import BED_CONFIGS, SIM_START


class Simulator:
    """Deterministic ward simulation clock.
    
    Keeps an internal time cursor initialized to SIM_START.
    Never calls datetime.now().
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.current_time = SIM_START
        self._init_schedule()

    def _init_schedule(self) -> None:
        """Initialize deterministic event stream for advance()."""
        self.rng = random.Random(self.seed)
        self.current_time = SIM_START
        self._generated_events: List[VitalsIn] = self._build_future_events()

    def _build_future_events(self) -> List[VitalsIn]:
        """Precompute scripted and routine vitals for 24 hours post SIM_START."""
        events: List[VitalsIn] = []
        rng = random.Random(self.seed + 1000)

        # 1. Scripted Story 1: Bed 7 post-op deterioration at SIM_START + 1h
        events.append(
            VitalsIn(
                patient_id=7,
                timestamp=SIM_START + timedelta(hours=1),
                source=Source.SIM,
                hr=98.0,
                sbp=112.0,
                dbp=70.0,
                rr=22.0,
                spo2=95.0,
                temp=37.4,
                on_oxygen=False,
                consciousness=Consciousness.ALERT,
            )
        )

        # 2. Scripted Story 3: Bed 12 crash reading at SIM_START + 5h
        events.append(
            VitalsIn(
                patient_id=12,
                timestamp=SIM_START + timedelta(hours=5),
                source=Source.SIM,
                hr=135.0,
                sbp=78.0,
                dbp=48.0,
                rr=28.0,
                spo2=86.0,
                temp=38.5,
                on_oxygen=False,
                consciousness=Consciousness.CONFUSION,
            )
        )

        # 3. Routine checks across the ward (4 to 6 hours cadence)
        # We generate scheduled check times for beds post SIM_START
        for bed_id, cfg in BED_CONFIGS.items():
            # For Bed 4: omit SBP reading up to SIM_START + 3h so BP remains 7h old
            # For Bed 7: already has scripted event at +1h; subsequent at +5h
            # For Bed 12: already has scripted crash at +5h; normal checks at +2h
            if bed_id == 7:
                # Later check at +4h (deteriorating RR and HR)
                t_check = SIM_START + timedelta(hours=4)
                events.append(
                    VitalsIn(
                        patient_id=7,
                        timestamp=t_check,
                        source=Source.SIM,
                        hr=104.0,
                        sbp=108.0,
                        dbp=68.0,
                        rr=24.0,
                        spo2=94.0,
                        temp=37.6,
                        on_oxygen=True,
                        consciousness=Consciousness.ALERT,
                    )
                )
                continue

            if bed_id == 12:
                # Normal check at +2h before crash at +5h
                t_check = SIM_START + timedelta(hours=2)
                events.append(
                    VitalsIn(
                        patient_id=12,
                        timestamp=t_check,
                        source=Source.SIM,
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
                continue

            if bed_id == 4:
                # Routine check at +2.5h where BP is omitted (only HR, RR, SpO2 taken)
                t_check = SIM_START + timedelta(hours=2, minutes=30)
                events.append(
                    VitalsIn(
                        patient_id=4,
                        timestamp=t_check,
                        source=Source.SIM,
                        hr=82.0,
                        sbp=None,
                        dbp=None,
                        rr=16.0,
                        spo2=97.0,
                        temp=36.7,
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )
                # Next check with BP at +6h (after the +5h crash demo)
                t_check2 = SIM_START + timedelta(hours=6)
                events.append(
                    VitalsIn(
                        patient_id=4,
                        timestamp=t_check2,
                        source=Source.SIM,
                        hr=80.0,
                        sbp=110.0,
                        dbp=68.0,
                        rr=16.0,
                        spo2=97.0,
                        temp=36.7,
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )
                continue

            # For all other beds, generate 1 to 3 checks across 12h
            # Bed 3 (COPD): keep stable RR 21-23, SpO2 90-92
            # Beds 5, 14 (COPD): stable chronic
            # Beds 9, 18 (Cardiac): stable chronic
            for hour_offset in [2.0, 6.0, 10.0]:
                jitter_min = rng.uniform(-15.0, 15.0)
                t_check = SIM_START + timedelta(hours=hour_offset, minutes=jitter_min)
                
                if cfg.role == "copd_chronic":
                    rr_val = round(rng.uniform(21.0, 23.0), 1)
                    spo2_val = round(rng.uniform(90.0, 92.0), 1)
                    hr_val = round(cfg.base_hr + rng.uniform(-2, 3), 1)
                    sbp_val = round(cfg.base_sbp + rng.uniform(-3, 3), 1)
                    dbp_val = round(cfg.base_dbp + rng.uniform(-2, 2), 1)
                elif cfg.role == "cardiac_chronic":
                    rr_val = round(cfg.base_rr + rng.uniform(-1, 1), 1)
                    spo2_val = round(cfg.base_spo2 + rng.uniform(-1, 1), 1)
                    hr_val = round(cfg.base_hr + rng.uniform(-3, 3), 1)
                    sbp_val = round(cfg.base_sbp + rng.uniform(-4, 4), 1)
                    dbp_val = round(cfg.base_dbp + rng.uniform(-2, 3), 1)
                else:
                    rr_val = round(cfg.base_rr + rng.uniform(-1.5, 1.5), 1)
                    spo2_val = round(min(100.0, cfg.base_spo2 + rng.uniform(-1, 1)), 1)
                    hr_val = round(cfg.base_hr + rng.uniform(-4, 4), 1)
                    sbp_val = round(cfg.base_sbp + rng.uniform(-4, 4), 1)
                    dbp_val = round(cfg.base_dbp + rng.uniform(-3, 3), 1)

                events.append(
                    VitalsIn(
                        patient_id=bed_id,
                        timestamp=t_check,
                        source=Source.SIM,
                        hr=hr_val,
                        sbp=sbp_val,
                        dbp=dbp_val,
                        rr=rr_val,
                        spo2=spo2_val,
                        temp=round(cfg.base_temp + rng.uniform(-0.2, 0.2), 1),
                        on_oxygen=False,
                        consciousness=Consciousness.ALERT,
                    )
                )

        # Sort all future events strictly by timestamp
        events.sort(key=lambda e: e.timestamp)
        return events

    def advance(self, to: datetime) -> List[VitalsIn]:
        """Advance simulation clock to target datetime.
        
        Returns all readings scheduled strictly after current_time and up to `to`.
        """
        if to <= self.current_time:
            return []

        due = [
            e for e in self._generated_events
            if self.current_time < e.timestamp <= to
        ]
        self.current_time = to
        return due

    def reset(self) -> None:
        """Reset simulation clock and state to SIM_START."""
        self._init_schedule()
