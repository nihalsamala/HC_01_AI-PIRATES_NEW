"""
Unit and regression tests for WardPulse Engine A (NEWS2, features, safety, risk).

Hand-built fixtures only: does NOT depend on the simulator.
"""

from datetime import datetime, timedelta
import pytest

from shared.schemas import (
    Condition,
    Consciousness,
    EngineConfig,
    Mode,
    Patient,
    RiskTier,
    TaskType,
    VitalName,
    VitalsBase,
    VitalsReading,
    Source,
)
from engine.features import extract_features, get_condition_prior
from engine.news2 import evaluate_ward_news2, news2_components, news2_score
from engine.risk import calculate_risk
from engine.safety import check_red_lines, is_crash


@pytest.fixture
def default_config():
    return EngineConfig()


@pytest.fixture
def general_patient():
    return Patient(
        id=1,
        bed=1,
        age=50,
        conditions=[],
        admitted_at=datetime(2026, 10, 20, 0, 0),
        display_name="Bed 1",
    )


@pytest.fixture
def copd_patient():
    return Patient(
        id=3,
        bed=3,
        age=68,
        conditions=[Condition.COPD],
        admitted_at=datetime(2026, 10, 19, 0, 0),
        display_name="Bed 3",
    )


@pytest.fixture
def post_op_patient():
    return Patient(
        id=7,
        bed=7,
        age=55,
        conditions=[Condition.POST_OP],
        admitted_at=datetime(2026, 10, 19, 12, 0),
        display_name="Bed 7",
    )


def test_news2_known_examples(default_config, general_patient, copd_patient):
    """Verify standard NEWS2 calculation against official RCP scoring bands."""
    # 1. Completely normal vitals -> score 0
    normal = VitalsBase(
        rr=16.0,
        spo2=98.0,
        on_oxygen=False,
        sbp=120.0,
        hr=72.0,
        consciousness=Consciousness.ALERT,
        temp=36.8,
    )
    assert news2_score(normal, general_patient, default_config) == 0

    # 2. Extreme parameter scores (score 3 each)
    # Severe tachypnea
    assert news2_components(VitalsBase(rr=28.0), general_patient, default_config)["scores"]["rr"] == 3
    # Severe bradypnea
    assert news2_components(VitalsBase(rr=8.0), general_patient, default_config)["scores"]["rr"] == 3
    # Severe hypoxia (Scale 1)
    assert news2_components(VitalsBase(spo2=90.0), general_patient, default_config)["scores"]["spo2"] == 3
    # Severe hypotension
    assert news2_components(VitalsBase(sbp=85.0), general_patient, default_config)["scores"]["sbp"] == 3
    # Severe hypertension
    assert news2_components(VitalsBase(sbp=225.0), general_patient, default_config)["scores"]["sbp"] == 3
    # Severe tachycardia
    assert news2_components(VitalsBase(hr=135.0), general_patient, default_config)["scores"]["hr"] == 3
    # Severe bradycardia
    assert news2_components(VitalsBase(hr=38.0), general_patient, default_config)["scores"]["hr"] == 3
    # Altered consciousness
    assert news2_components(VitalsBase(consciousness=Consciousness.CONFUSION), general_patient, default_config)["scores"]["consciousness"] == 3
    # Severe hypothermia
    assert news2_components(VitalsBase(temp=34.8), general_patient, default_config)["scores"]["temp"] == 3
    # Hyperthermia (score 2 for temp >= 39.1)
    assert news2_components(VitalsBase(temp=39.4), general_patient, default_config)["scores"]["temp"] == 2

    # 3. Supplemental oxygen -> +2 points
    o2_reading = VitalsBase(rr=16.0, spo2=98.0, on_oxygen=True, sbp=120.0, hr=72.0)
    assert news2_score(o2_reading, general_patient, default_config) == 2

    # 4. SpO2 Scale 2 for COPD
    copd_cfg = EngineConfig(news2_spo2_scale2_for_copd=True)
    scale2_normal = VitalsBase(spo2=90.0, on_oxygen=False)
    # Under scale 2, SpO2 90% on air scores 0 (target 88-92)
    comp_scale2 = news2_components(scale2_normal, copd_patient, copd_cfg)
    assert comp_scale2["scores"]["spo2"] == 0
    assert comp_scale2["scale2_used"] is True


def test_news2_missing_vitals_handled(default_config, general_patient):
    """Missing vitals must score 0 and be recorded in missing list."""
    partial = VitalsBase(hr=76.0, sbp=120.0)
    comp = news2_components(partial, general_patient, default_config)
    assert comp["scores"]["hr"] == 0
    assert comp["scores"]["sbp"] == 0
    assert "rr" in comp["missing"]
    assert "spo2" in comp["missing"]
    assert "temp" in comp["missing"]
    assert comp["total"] == 0

    none_reading = None
    comp_none = news2_components(none_reading, general_patient, default_config)
    assert comp_none["total"] == 0
    assert len(comp_none["missing"]) == 7


def test_evaluate_ward_news2_pipeline(default_config):
    """evaluate_ward_news2 should create active Tasks for patients meeting alert threshold."""
    now = datetime(2026, 10, 20, 10, 0)
    p1 = Patient(id=1, bed=1, age=50, conditions=[], admitted_at=now, display_name="Bed 1")
    p2 = Patient(id=2, bed=2, age=60, conditions=[], admitted_at=now, display_name="Bed 2")
    p3 = Patient(id=3, bed=3, age=70, conditions=[], admitted_at=now, display_name="Bed 3")

    vitals = {
        1: [VitalsReading(id=1, patient_id=1, timestamp=now, source=Source.MANUAL, hr=72.0, sbp=120.0, rr=16.0, spo2=98.0)],
        # p2: RR 22 (2 pts) + SpO2 91 (3 pts) = 5 pts (meets threshold 5)
        2: [VitalsReading(id=2, patient_id=2, timestamp=now, source=Source.MANUAL, hr=80.0, sbp=125.0, rr=22.0, spo2=91.0)],
        # p3: SBP 85 (3 pts alone) -> raises alert via single-score-3 rule
        3: [VitalsReading(id=3, patient_id=3, timestamp=now, source=Source.MANUAL, hr=75.0, sbp=85.0, rr=16.0, spo2=98.0)],
    }

    eval_result = evaluate_ward_news2([p1, p2, p3], vitals, now, default_config)
    assert eval_result.tasks.mode == Mode.NEWS2
    assert eval_result.tasks.budget_k is None

    active_task_beds = [t.bed for t in eval_result.tasks.active]
    assert 2 in active_task_beds
    assert 3 in active_task_beds
    assert 1 not in active_task_beds
    assert len(eval_result.tasks.emergency) == 0


def test_copd_patient_vs_post_op_patient(default_config, copd_patient, post_op_patient):
    """COPD patient at baseline (RR 22, SpO2 91) has LOW/MEDIUM risk while deteriorating post-op is HIGH."""
    now = datetime(2026, 10, 20, 7, 0)

    # 1. Stable COPD patient (Bed 3)
    copd_readings = [
        VitalsReading(id=101, patient_id=3, timestamp=now - timedelta(hours=16), source=Source.SIM, hr=82.0, sbp=126.0, dbp=80.0, rr=22.0, spo2=91.0, temp=36.8),
        VitalsReading(id=102, patient_id=3, timestamp=now - timedelta(hours=11), source=Source.SIM, hr=80.0, sbp=125.0, dbp=80.0, rr=21.0, spo2=91.0, temp=36.8),
        VitalsReading(id=103, patient_id=3, timestamp=now - timedelta(hours=6), source=Source.SIM, hr=82.0, sbp=126.0, dbp=80.0, rr=23.0, spo2=90.0, temp=36.8),
        VitalsReading(id=104, patient_id=3, timestamp=now - timedelta(hours=1), source=Source.SIM, hr=81.0, sbp=125.0, dbp=80.0, rr=22.0, spo2=91.0, temp=36.8),
    ]
    copd_feats = extract_features(copd_patient, copd_readings, now, default_config)
    copd_score, copd_tier, copd_crash, copd_reasons = calculate_risk(
        copd_feats, copd_readings[-1], copd_patient, default_config
    )

    # Under WardPulse, stable COPD baseline keeps risk LOW
    assert copd_tier in (RiskTier.LOW, RiskTier.MEDIUM)
    assert copd_score < default_config.tier_high
    assert copd_crash is False

    # 2. Deteriorating Post-op patient (Bed 7): RR 14 -> 17 -> 22 with pulse rising
    post_op_readings = [
        VitalsReading(id=201, patient_id=7, timestamp=now - timedelta(hours=15), source=Source.SIM, hr=72.0, sbp=122.0, dbp=78.0, rr=14.0, spo2=98.0, temp=36.8),
        VitalsReading(id=202, patient_id=7, timestamp=now - timedelta(hours=10), source=Source.SIM, hr=76.0, sbp=120.0, dbp=76.0, rr=14.0, spo2=97.0, temp=36.8),
        VitalsReading(id=203, patient_id=7, timestamp=now - timedelta(hours=5), source=Source.SIM, hr=84.0, sbp=116.0, dbp=74.0, rr=17.0, spo2=96.0, temp=37.0),
        VitalsReading(id=204, patient_id=7, timestamp=now, source=Source.SIM, hr=98.0, sbp=112.0, dbp=70.0, rr=22.0, spo2=95.0, temp=37.4),
    ]
    post_op_feats = extract_features(post_op_patient, post_op_readings, now, default_config)
    post_op_score, post_op_tier, post_op_crash, post_op_reasons = calculate_risk(
        post_op_feats, post_op_readings[-1], post_op_patient, default_config
    )

    # Post-op patient rising to RR 22 with tachycardia must be HIGH risk
    assert post_op_tier == RiskTier.HIGH
    assert post_op_score >= default_config.tier_high


def test_crash_vitals_are_crash(default_config, general_patient):
    """Story 3 vitals (SBP 78, HR 135, SpO2 86) must be identified as crash."""
    crash_reading = VitalsBase(
        sbp=78.0,
        dbp=48.0,
        hr=135.0,
        spo2=86.0,
        rr=28.0,
        temp=38.5,
        consciousness=Consciousness.CONFUSION,
    )
    assert is_crash(crash_reading) is True

    now = datetime(2026, 10, 20, 11, 0)
    reading_obj = VitalsReading(
        id=999,
        patient_id=1,
        timestamp=now,
        source=Source.SIM,
        hr=135.0,
        sbp=78.0,
        dbp=48.0,
        rr=28.0,
        spo2=86.0,
        temp=38.5,
        consciousness=Consciousness.CONFUSION,
    )
    feats = extract_features(general_patient, [reading_obj], now, default_config)
    score, tier, crash_flag, reasons = calculate_risk(
        feats, reading_obj, general_patient, default_config
    )

    assert crash_flag is True
    assert tier == RiskTier.CRITICAL
    assert score >= 0.95
    assert any("CRASH" in r for r in reasons)


def test_baseline_never_suppresses_red_line_breach(default_config):
    """Personal baseline familiarity must never suppress an absolute red-line breach."""
    now = datetime(2026, 10, 20, 10, 0)
    # A patient whose baseline BP is low-ish (105 mmHg)
    patient = Patient(id=1, bed=1, age=60, conditions=[], admitted_at=now - timedelta(days=2))
    past_readings = [
        VitalsReading(id=1, patient_id=1, timestamp=now - timedelta(hours=10), source=Source.SIM, hr=75.0, sbp=105.0, dbp=68.0, rr=16.0, spo2=98.0),
        VitalsReading(id=2, patient_id=1, timestamp=now - timedelta(hours=6), source=Source.SIM, hr=74.0, sbp=102.0, dbp=66.0, rr=16.0, spo2=97.0),
        VitalsReading(id=3, patient_id=1, timestamp=now - timedelta(hours=2), source=Source.SIM, hr=76.0, sbp=100.0, dbp=65.0, rr=16.0, spo2=97.0),
    ]

    # Acute drop into red line: SBP 88 mmHg (NEWS2 score 3 red line)
    acute_drop = VitalsReading(
        id=4, patient_id=1, timestamp=now, source=Source.SIM,
        hr=78.0, sbp=88.0, dbp=58.0, rr=16.0, spo2=97.0,
    )
    all_readings = past_readings + [acute_drop]
    feats = extract_features(patient, all_readings, now, default_config)
    score, tier, crash_flag, reasons = calculate_risk(feats, acute_drop, patient, default_config)

    # Must be at least HIGH risk because SBP <= 90 is a hard red line
    assert tier in (RiskTier.HIGH, RiskTier.CRITICAL)
    assert score >= default_config.tier_high
    assert any("Critical systolic blood pressure" in r for r in reasons)


def test_all_none_readings_do_not_raise(default_config, general_patient):
    """Empty and all-None readings should be handled safely without exceptions."""
    none_base = VitalsBase()
    is_breached, reasons = check_red_lines(none_base, general_patient, default_config)
    assert is_breached is False
    assert is_crash(none_base) is False

    now = datetime(2026, 10, 20, 10, 0)
    feats = extract_features(general_patient, [], now, default_config)
    score, tier, crash_flag, reasons = calculate_risk(feats, None, general_patient, default_config)
    assert score == 0.0
    assert tier == RiskTier.LOW
    assert crash_flag is False


def test_cold_start_patient_single_reading(default_config, general_patient):
    """A newly admitted patient with only 1 reading blends with condition prior gracefully."""
    now = datetime(2026, 10, 20, 10, 0)
    single_reading = VitalsReading(
        id=1,
        patient_id=general_patient.id,
        timestamp=now,
        source=Source.MANUAL,
        hr=76.0,
        sbp=122.0,
        dbp=78.0,
        rr=15.0,
        spo2=98.0,
        temp=36.7,
    )
    feats = extract_features(general_patient, [single_reading], now, default_config)
    # 0 baseline history items because exclude_latest=1 excludes the sole reading
    assert feats.baselines[VitalName.RR].n_readings_used == 0
    # Effective baseline uses condition prior
    prior = get_condition_prior(general_patient)
    assert feats.baselines[VitalName.RR].effective_baseline == prior[VitalName.RR]

    score, tier, crash_flag, reasons = calculate_risk(feats, single_reading, general_patient, default_config)
    assert 0.0 <= score <= 1.0
    assert tier == RiskTier.LOW
    assert crash_flag is False
