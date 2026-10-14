"""
Test suite for Live Story 4 (Typed-in COPD deterioration).

Validates:
- Bed 5 (COPD, stable history) receives an active task card with a COPD-specific focus reason
  when SpO2 falls to 88% while RR remains at their chronic normal (22 bpm).
- Bed 6 (non-COPD control patient) given the exact same numbers does NOT receive the COPD-boosted reason.
- Hand-built test fixture in tests/fixtures.py guarantees zero dependency on simulator state.
"""

from datetime import datetime
import pytest

from shared.schemas import EngineConfig, TaskType
from engine.pipeline import evaluate_ward
from tests.fixtures import FIXTURE_BASE_TIME, build_story4_fixtures


def test_story4_copd_active_card_and_reason():
    """Bed 5 (COPD) receives active card with COPD focus reason; control Bed 6 does not."""
    now = FIXTURE_BASE_TIME
    config = EngineConfig()

    patients, vitals_dict = build_story4_fixtures(now)
    p5 = next(p for p in patients if p.bed == 5)
    p6 = next(p for p in patients if p.bed == 6)

    # 1. Evaluate Bed 5 (COPD deterioration)
    ev5 = evaluate_ward([p5], {5: vitals_dict[5]}, now, config, [])
    b5_active = [t for t in ev5.tasks.active if t.bed == 5]
    assert len(b5_active) > 0, "Bed 5 (COPD) must receive an active task card upon hypoxia breach"

    b5_page_doc = next((t for t in b5_active if t.type == TaskType.PAGE_DOCTOR), None)
    assert b5_page_doc is not None, "Bed 5 must receive a page_doctor card for critical COPD hypoxia"
    assert "COPD" in b5_page_doc.reason, f"Bed 5 card reason must state COPD focus: {b5_page_doc.reason}"
    assert "Critical hypoxia for COPD" in b5_page_doc.reason

    # 2. Evaluate Bed 6 (Control patient given same vitals)
    ev6 = evaluate_ward([p6], {6: vitals_dict[6]}, now, config, [])
    b6_active = [t for t in ev6.tasks.active if t.bed == 6]
    assert len(b6_active) > 0

    b6_page_doc = next((t for t in b6_active if t.type == TaskType.PAGE_DOCTOR), None)
    assert b6_page_doc is not None
    # Bed 6 control must NOT receive COPD-boosted reason
    assert "COPD" not in b6_page_doc.reason, f"Bed 6 (control) must NOT receive COPD reason: {b6_page_doc.reason}"
    assert "Critical hypoxia: SpO2" in b6_page_doc.reason


def test_story4_assessment_reasons():
    """Assessments explicitly distinguish COPD-specific red line from general hypoxia."""
    now = FIXTURE_BASE_TIME
    config = EngineConfig()

    patients, vitals_dict = build_story4_fixtures(now)
    p5 = next(p for p in patients if p.bed == 5)
    p6 = next(p for p in patients if p.bed == 6)

    ev = evaluate_ward(patients, vitals_dict, now, EngineConfig(k_budget=4), [])

    a5 = next(a for a in ev.assessments if a.bed == 5)
    a6 = next(a for a in ev.assessments if a.bed == 6)

    # Bed 5 assessment includes COPD threshold reason
    assert any("Critical hypoxia for COPD" in r for r in a5.reasons)
    # Bed 6 does not mention COPD
    assert not any("COPD" in r for r in a6.reasons)
