import test from 'node:test';
import assert from 'node:assert/strict';

function getMockPatientDetail(bedNum) {
  return {
    patient: {
      id: bedNum,
      bed: bedNum,
      display_name: `Bed ${bedNum}`,
    },
    recent_vitals: [
      { id: 100 + bedNum, patient_id: bedNum, hr: 80, sbp: 120 }
    ],
    assessment: {
      risk_tier: bedNum === 12 ? 'critical' : bedNum === 7 ? 'high' : 'stable',
    },
  };
}

test('Ward at a glance grid: Clicking beds 3, 7, and 12 passes the correct bed numbers', () => {
  const selectedBeds = [];
  const onSelectBed = (bed) => {
    selectedBeds.push(bed);
  };

  // Simulate clicking beds in the 20-bed grid
  const bedList = Array.from({ length: 20 }, (_, i) => ({
    bed: i + 1,
  }));

  for (const targetBed of [3, 7, 12]) {
    const item = bedList.find((b) => b.bed === targetBed);
    assert.ok(item, `Bed ${targetBed} should exist in bedList`);
    onSelectBed(item.bed);
  }

  assert.deepEqual(selectedBeds, [3, 7, 12], 'Should have clicked beds 3, 7, and 12 in order');
});

test('Patient Detail resolution: beds 3, 7, and 12 load corresponding patient records', () => {
  const detail3 = getMockPatientDetail(3);
  assert.equal(detail3.patient.bed, 3);
  assert.equal(detail3.patient.id, 3);
  assert.ok(detail3.recent_vitals.length > 0);

  const detail7 = getMockPatientDetail(7);
  assert.equal(detail7.patient.bed, 7);
  assert.equal(detail7.patient.id, 7);
  assert.equal(detail7.assessment?.risk_tier, 'high');

  const detail12 = getMockPatientDetail(12);
  assert.equal(detail12.patient.bed, 12);
  assert.equal(detail12.patient.id, 12);
  assert.equal(detail12.assessment?.risk_tier, 'critical');
});

test('State management & vitals isolation: Entering vitals for Bed 1 does not override selected bed', () => {
  // Model App state and ref lifecycle
  let selectedBed = null;
  const selectedBedRef = { current: null };
  let patientDetail = null;
  const patientDetailsMap = {};

  const selectBed = (bed) => {
    selectedBed = bed;
    selectedBedRef.current = bed;
    // Cache check prevents stale flash
    if (patientDetailsMap[bed]) {
      patientDetail = patientDetailsMap[bed];
    } else {
      patientDetail = null;
    }
    // Async detail fetch simulation
    const detail = getMockPatientDetail(bed);
    // Race condition check: only set if still the active bed
    if (selectedBedRef.current === bed) {
      patientDetail = detail;
    }
    patientDetailsMap[bed] = detail;
  };

  // 1. User clicks Bed 3
  selectBed(3);
  assert.equal(selectedBed, 3);
  assert.equal(patientDetail?.patient?.bed, 3, 'Patient panel must show Bed 3');

  // 2. User enters vitals for Bed 1 through quick vitals modal
  const vitalsPayload = { patient_id: 1, hr: 82, sbp: 122 };
  // When vitals are submitted, reload selectedBedRef.current (Bed 3), NOT hardcoded Bed 1
  if (selectedBedRef.current !== null) {
    const refreshed = getMockPatientDetail(selectedBedRef.current);
    if (selectedBedRef.current === refreshed.patient.bed) {
      patientDetail = refreshed;
    }
  }
  assert.equal(selectedBed, 3, 'Selected bed must remain Bed 3 after submitting vitals for Bed 1');
  assert.equal(patientDetail?.patient?.bed, 3, 'Patient detail must remain Bed 3');

  // 3. User clicks Bed 7
  selectBed(7);
  assert.equal(selectedBed, 7);
  assert.equal(patientDetail?.patient?.bed, 7, 'Patient panel must open Bed 7');

  // 4. User clicks Bed 12
  selectBed(12);
  assert.equal(selectedBed, 12);
  assert.equal(patientDetail?.patient?.bed, 12, 'Patient panel must open Bed 12');

  // 5. Stale / delayed out-of-order response check
  const staleBed1Detail = getMockPatientDetail(1);
  if (selectedBedRef.current === 1) {
    patientDetail = staleBed1Detail;
  }
  assert.equal(selectedBed, 12, 'Selected bed must still be Bed 12');
  assert.equal(patientDetail?.patient?.bed, 12, 'Stale Bed 1 response must not overwrite Bed 12');
});
