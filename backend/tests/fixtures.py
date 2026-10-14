"""
Hand-built test fixtures for WardPulse Engine contract tests.

Contains static patient definitions and reading histories for:
- Story 1 (Bed 3 COPD baseline vs Bed 7 post-op deterioration)
- Story 2 (Bed 4 stale BP)
- Story 3 (Bed 12 crash bypass)
- 10-abnormal-patient ward for testing attention budget K=2.

DOES NOT import or depend on the simulator.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from shared.schemas import (
    Condition,
    Consciousness,
    Patient,
    Source,
    VitalsReading,
)

FIXTURE_BASE_TIME = datetime(2026, 10, 20, 6, 0, 0)


def build_story1_fixtures(now: datetime) -> Tuple[List[Patient], Dict[int, List[VitalsReading]]]:
    """Story 1: Bed 3 (COPD stable at RR 22) vs Bed 7 (Post-op rising to RR 22)."""
    p3 = Patient(
        id=3,
        bed=3,
        age=68,
        conditions=[Condition.COPD],
        admitted_at=now - timedelta(days=2),
        display_name="Bed 3",
    )
    p7 = Patient(
        id=7,
        bed=7,
        age=54,
        conditions=[Condition.POST_OP],
        admitted_at=now - timedelta(days=1),
        display_name="Bed 7",
    )

    # Bed 3: stable COPD baseline at RR 22, SpO2 91%
    vitals_bed3 = [
        VitalsReading(id=301, patient_id=3, timestamp=now - timedelta(hours=18), source=Source.MANUAL, hr=82.0, sbp=126.0, dbp=80.0, rr=22.0, spo2=91.0, temp=36.8),
        VitalsReading(id=302, patient_id=3, timestamp=now - timedelta(hours=12), source=Source.MANUAL, hr=80.0, sbp=125.0, dbp=80.0, rr=21.0, spo2=91.0, temp=36.8),
        VitalsReading(id=303, patient_id=3, timestamp=now - timedelta(hours=6), source=Source.MANUAL, hr=82.0, sbp=126.0, dbp=80.0, rr=23.0, spo2=90.0, temp=36.8),
        VitalsReading(id=304, patient_id=3, timestamp=now, source=Source.MANUAL, hr=81.0, sbp=125.0, dbp=80.0, rr=22.0, spo2=91.0, temp=36.8),
    ]

    # Bed 7: post-op RR rising 14 -> 14 -> 15 -> 17 -> 22, pulse rising 72 -> 98
    vitals_bed7 = [
        VitalsReading(id=701, patient_id=7, timestamp=now - timedelta(hours=18), source=Source.MANUAL, hr=72.0, sbp=122.0, dbp=78.0, rr=14.0, spo2=98.0, temp=36.8),
        VitalsReading(id=702, patient_id=7, timestamp=now - timedelta(hours=12), source=Source.MANUAL, hr=76.0, sbp=120.0, dbp=76.0, rr=14.0, spo2=97.0, temp=36.8),
        VitalsReading(id=703, patient_id=7, timestamp=now - timedelta(hours=6), source=Source.MANUAL, hr=84.0, sbp=116.0, dbp=74.0, rr=17.0, spo2=96.0, temp=37.0),
        VitalsReading(id=704, patient_id=7, timestamp=now, source=Source.MANUAL, hr=98.0, sbp=112.0, dbp=70.0, rr=22.0, spo2=95.0, temp=37.4),
    ]

    return [p3, p7], {3: vitals_bed3, 7: vitals_bed7}


def build_story2_fixtures(now: datetime) -> Tuple[List[Patient], Dict[int, List[VitalsReading]]]:
    """Story 2: Bed 4 has stale BP (taken 7h ago), other vitals recent."""
    p4 = Patient(
        id=4,
        bed=4,
        age=62,
        conditions=[],
        admitted_at=now - timedelta(days=2),
        display_name="Bed 4",
    )

    # BP falling earlier (128 -> 112); last BP at now - 7h; other vitals retaken at now - 1h
    vitals_bed4 = [
        VitalsReading(id=401, patient_id=4, timestamp=now - timedelta(hours=20), source=Source.MANUAL, hr=74.0, sbp=128.0, dbp=80.0, rr=15.0, spo2=98.0, temp=36.6),
        VitalsReading(id=402, patient_id=4, timestamp=now - timedelta(hours=14), source=Source.MANUAL, hr=76.0, sbp=120.0, dbp=76.0, rr=16.0, spo2=97.0, temp=36.7),
        # Last BP taken here (7 hours before now):
        VitalsReading(id=403, patient_id=4, timestamp=now - timedelta(hours=7), source=Source.MANUAL, hr=80.0, sbp=112.0, dbp=70.0, rr=16.0, spo2=97.0, temp=36.7),
        # BP omitted 1 hour ago:
        VitalsReading(id=404, patient_id=4, timestamp=now - timedelta(hours=1), source=Source.MANUAL, hr=82.0, sbp=None, dbp=None, rr=16.0, spo2=97.0, temp=36.8),
    ]

    return [p4], {4: vitals_bed4}


def build_story3_fixtures(now: datetime) -> Tuple[List[Patient], Dict[int, List[VitalsReading]]]:
    """Story 3: Bed 12 has unequivocal crash vitals while Beds 7 and 4 fill K=2 slots."""
    # Combine Beds 7, 4, and 12
    p7 = Patient(id=7, bed=7, age=54, conditions=[Condition.POST_OP], admitted_at=now - timedelta(days=1), display_name="Bed 7")
    p4 = Patient(id=4, bed=4, age=62, conditions=[], admitted_at=now - timedelta(days=2), display_name="Bed 4")
    p12 = Patient(id=12, bed=12, age=70, conditions=[], admitted_at=now - timedelta(days=1), display_name="Bed 12")

    v_bed7 = [
        VitalsReading(id=701, patient_id=7, timestamp=now - timedelta(hours=18), source=Source.MANUAL, hr=72.0, sbp=122.0, dbp=78.0, rr=14.0, spo2=98.0, temp=36.8),
        VitalsReading(id=702, patient_id=7, timestamp=now - timedelta(hours=12), source=Source.MANUAL, hr=76.0, sbp=120.0, dbp=76.0, rr=14.0, spo2=97.0, temp=36.8),
        VitalsReading(id=703, patient_id=7, timestamp=now - timedelta(hours=6), source=Source.MANUAL, hr=84.0, sbp=116.0, dbp=74.0, rr=17.0, spo2=96.0, temp=37.0),
        VitalsReading(id=704, patient_id=7, timestamp=now, source=Source.MANUAL, hr=98.0, sbp=112.0, dbp=70.0, rr=22.0, spo2=95.0, temp=37.4),
    ]

    v_bed4 = [
        VitalsReading(id=401, patient_id=4, timestamp=now - timedelta(hours=20), source=Source.MANUAL, hr=74.0, sbp=128.0, dbp=80.0, rr=15.0, spo2=98.0, temp=36.6),
        VitalsReading(id=402, patient_id=4, timestamp=now - timedelta(hours=14), source=Source.MANUAL, hr=76.0, sbp=120.0, dbp=76.0, rr=16.0, spo2=97.0, temp=36.7),
        VitalsReading(id=403, patient_id=4, timestamp=now - timedelta(hours=7), source=Source.MANUAL, hr=80.0, sbp=112.0, dbp=70.0, rr=16.0, spo2=97.0, temp=36.7),
        VitalsReading(id=404, patient_id=4, timestamp=now - timedelta(hours=1), source=Source.MANUAL, hr=82.0, sbp=None, dbp=None, rr=16.0, spo2=97.0, temp=36.8),
    ]

    # Bed 12 crash reading
    v_bed12 = [
        VitalsReading(id=1201, patient_id=12, timestamp=now - timedelta(hours=4), source=Source.MANUAL, hr=72.0, sbp=122.0, dbp=76.0, rr=15.0, spo2=98.0, temp=36.6),
        VitalsReading(id=1202, patient_id=12, timestamp=now, source=Source.MANUAL, hr=135.0, sbp=78.0, dbp=48.0, rr=28.0, spo2=86.0, temp=38.5, consciousness=Consciousness.CONFUSION),
    ]

    return [p7, p4, p12], {7: v_bed7, 4: v_bed4, 12: v_bed12}


def build_10_abnormal_patients_fixtures(now: datetime) -> Tuple[List[Patient], Dict[int, List[VitalsReading]]]:
    """10 patients with deteriorating / abnormal vitals to test K-budget constraint."""
    patients = []
    vitals = {}

    for i in range(1, 11):
        p = Patient(
            id=i,
            bed=i,
            age=50 + i,
            conditions=[Condition.POST_OP],
            admitted_at=now - timedelta(days=1),
            display_name=f"Bed {i}",
        )
        patients.append(p)

        # Each patient has deteriorating vitals that trigger high risk
        readings = [
            VitalsReading(
                id=i * 10 + 1,
                patient_id=i,
                timestamp=now - timedelta(hours=4),
                source=Source.MANUAL,
                hr=75.0,
                sbp=120.0,
                dbp=76.0,
                rr=15.0,
                spo2=98.0,
                temp=36.7,
            ),
            VitalsReading(
                id=i * 10 + 2,
                patient_id=i,
                timestamp=now,
                source=Source.MANUAL,
                hr=95.0 + i,
                sbp=110.0 - i,
                dbp=68.0,
                rr=22.0,
                spo2=94.0,
                temp=37.5,
            ),
        ]
        vitals[i] = readings

    return patients, vitals


def build_story4_fixtures(now: datetime) -> Tuple[List[Patient], Dict[int, List[VitalsReading]]]:
    """Story 4 (Typed-in): Bed 5 (COPD, SpO2 falling to 88% while RR normal) vs Bed 6 (non-COPD control)."""
    p5 = Patient(
        id=5,
        bed=5,
        age=74,
        conditions=[Condition.COPD],
        admitted_at=now - timedelta(days=2),
        display_name="Bed 5",
    )
    p6 = Patient(
        id=6,
        bed=6,
        age=39,
        conditions=[],
        admitted_at=now - timedelta(days=1),
        display_name="Bed 6",
    )

    # Bed 5 (COPD): chronic stable RR 22, SpO2 91%
    vitals_bed5 = [
        VitalsReading(id=501, patient_id=5, timestamp=now - timedelta(hours=18), source=Source.MANUAL, hr=80.0, sbp=124.0, dbp=78.0, rr=22.0, spo2=91.0, temp=36.7),
        VitalsReading(id=502, patient_id=5, timestamp=now - timedelta(hours=12), source=Source.MANUAL, hr=79.0, sbp=125.0, dbp=78.0, rr=21.0, spo2=92.0, temp=36.7),
        VitalsReading(id=503, patient_id=5, timestamp=now - timedelta(hours=6), source=Source.MANUAL, hr=81.0, sbp=123.0, dbp=77.0, rr=22.0, spo2=91.0, temp=36.8),
        # New reading: SpO2 drops to 88% while RR remains at baseline 22
        VitalsReading(id=504, patient_id=5, timestamp=now, source=Source.MANUAL, hr=80.0, sbp=124.0, dbp=78.0, rr=22.0, spo2=88.0, temp=36.7, on_oxygen=True),
    ]

    # Bed 6 (Control, general): baseline RR 14, SpO2 99%
    vitals_bed6 = [
        VitalsReading(id=601, patient_id=6, timestamp=now - timedelta(hours=18), source=Source.MANUAL, hr=68.0, sbp=118.0, dbp=74.0, rr=14.0, spo2=99.0, temp=36.5),
        VitalsReading(id=602, patient_id=6, timestamp=now - timedelta(hours=12), source=Source.MANUAL, hr=69.0, sbp=117.0, dbp=73.0, rr=14.0, spo2=98.0, temp=36.6),
        VitalsReading(id=603, patient_id=6, timestamp=now - timedelta(hours=6), source=Source.MANUAL, hr=67.0, sbp=119.0, dbp=75.0, rr=15.0, spo2=99.0, temp=36.5),
        # Same new reading numbers applied to Bed 6
        VitalsReading(id=604, patient_id=6, timestamp=now, source=Source.MANUAL, hr=80.0, sbp=124.0, dbp=78.0, rr=22.0, spo2=88.0, temp=36.7, on_oxygen=True),
    ]

    return [p5, p6], {5: vitals_bed5, 6: vitals_bed6}

