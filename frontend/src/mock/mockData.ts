import {
  Condition,
  Patient,
  PatientAssessment,
  PatientDetail,
  SimState,
  Task,
  TasksResponse,
  VitalsReading,
  WardBed,
  WardOverview,
} from '../types';

export const MOCK_SIM_START = '2026-10-20T06:00:00';
export const MOCK_SIM_CURRENT = '2026-10-20T11:05:00';

export const MOCK_PATIENTS: Patient[] = [
  { id: 1, bed: 1, age: 62, conditions: [], admitted_at: '2026-10-18T08:00:00', display_name: 'Patient 1' },
  { id: 2, bed: 2, age: 55, conditions: ['cardiac'], admitted_at: '2026-10-18T10:00:00', display_name: 'Patient 2' },
  { id: 3, bed: 3, age: 71, conditions: ['copd'], admitted_at: '2026-10-17T14:00:00', display_name: 'Patient 3' },
  { id: 4, bed: 4, age: 68, conditions: [], admitted_at: '2026-10-18T12:00:00', display_name: 'Patient 4' },
  { id: 5, bed: 5, age: 49, conditions: [], admitted_at: '2026-10-19T09:00:00', display_name: 'Patient 5' },
  { id: 6, bed: 6, age: 74, conditions: ['cardiac'], admitted_at: '2026-10-17T11:00:00', display_name: 'Patient 6' },
  { id: 7, bed: 7, age: 58, conditions: ['post_op'], admitted_at: '2026-10-19T07:00:00', display_name: 'Patient 7' },
  { id: 8, bed: 8, age: 80, conditions: ['copd'], admitted_at: '2026-10-16T15:00:00', display_name: 'Patient 8' },
  { id: 9, bed: 9, age: 45, conditions: [], admitted_at: '2026-10-19T13:00:00', display_name: 'Patient 9' },
  { id: 10, bed: 10, age: 63, conditions: [], admitted_at: '2026-10-18T16:00:00', display_name: 'Patient 10' },
  { id: 11, bed: 11, age: 52, conditions: ['post_op'], admitted_at: '2026-10-19T10:00:00', display_name: 'Patient 11' },
  { id: 12, bed: 12, age: 77, conditions: ['cardiac'], admitted_at: '2026-10-17T09:00:00', display_name: 'Patient 12' },
  { id: 13, bed: 13, age: 65, conditions: [], admitted_at: '2026-10-18T18:00:00', display_name: 'Patient 13' },
  { id: 14, bed: 14, age: 59, conditions: [], admitted_at: '2026-10-19T06:00:00', display_name: 'Patient 14' },
  { id: 15, bed: 15, age: 82, conditions: ['copd', 'cardiac'], admitted_at: '2026-10-16T12:00:00', display_name: 'Patient 15' },
  { id: 16, bed: 16, age: 41, conditions: ['post_op'], admitted_at: '2026-10-19T14:00:00', display_name: 'Patient 16' },
  { id: 17, bed: 17, age: 70, conditions: [], admitted_at: '2026-10-18T07:00:00', display_name: 'Patient 17' },
  { id: 18, bed: 18, age: 66, conditions: ['cardiac'], admitted_at: '2026-10-17T20:00:00', display_name: 'Patient 18' },
  { id: 19, bed: 19, age: 73, conditions: ['copd'], admitted_at: '2026-10-17T08:00:00', display_name: 'Patient 19' },
  { id: 20, bed: 20, age: 60, conditions: [], admitted_at: '2026-10-19T08:00:00', display_name: 'Patient 20' },
];

export const MOCK_WARD_BEDS: WardBed[] = [
  { patient_id: 1, bed: 1, conditions: [], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 1.2, has_open_task: false },
  { patient_id: 2, bed: 2, conditions: ['cardiac'], status: 'watch', risk_tier: 'medium', data_stale: false, hours_since_last_vitals: 2.1, has_open_task: false },
  { patient_id: 3, bed: 3, conditions: ['copd'], status: 'watch', risk_tier: 'medium', data_stale: false, hours_since_last_vitals: 1.5, has_open_task: false },
  { patient_id: 4, bed: 4, conditions: [], status: 'action', risk_tier: 'medium', data_stale: true, hours_since_last_vitals: 7.2, has_open_task: true },
  { patient_id: 5, bed: 5, conditions: [], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 3.0, has_open_task: false },
  { patient_id: 6, bed: 6, conditions: ['cardiac'], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 2.4, has_open_task: false },
  { patient_id: 7, bed: 7, conditions: ['post_op'], status: 'action', risk_tier: 'high', data_stale: false, hours_since_last_vitals: 0.8, has_open_task: true },
  { patient_id: 8, bed: 8, conditions: ['copd'], status: 'watch', risk_tier: 'medium', data_stale: true, hours_since_last_vitals: 6.5, has_open_task: true },
  { patient_id: 9, bed: 9, conditions: [], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 1.8, has_open_task: false },
  { patient_id: 10, bed: 10, conditions: [], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 2.9, has_open_task: false },
  { patient_id: 11, bed: 11, conditions: ['post_op'], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 1.1, has_open_task: false },
  { patient_id: 12, bed: 12, conditions: ['cardiac'], status: 'critical', risk_tier: 'critical', data_stale: false, hours_since_last_vitals: 0.1, has_open_task: true },
  { patient_id: 13, bed: 13, conditions: [], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 3.5, has_open_task: false },
  { patient_id: 14, bed: 14, conditions: [], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 2.2, has_open_task: false },
  { patient_id: 15, bed: 15, conditions: ['copd', 'cardiac'], status: 'watch', risk_tier: 'medium', data_stale: true, hours_since_last_vitals: 5.8, has_open_task: false },
  { patient_id: 16, bed: 16, conditions: ['post_op'], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 1.0, has_open_task: false },
  { patient_id: 17, bed: 17, conditions: [], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 2.6, has_open_task: false },
  { patient_id: 18, bed: 18, conditions: ['cardiac'], status: 'watch', risk_tier: 'medium', data_stale: false, hours_since_last_vitals: 1.9, has_open_task: false },
  { patient_id: 19, bed: 19, conditions: ['copd'], status: 'watch', risk_tier: 'medium', data_stale: true, hours_since_last_vitals: 7.0, has_open_task: false },
  { patient_id: 20, bed: 20, conditions: [], status: 'stable', risk_tier: 'low', data_stale: false, hours_since_last_vitals: 2.0, has_open_task: false },
];

export const MOCK_WARD_OVERVIEW: WardOverview = {
  now: MOCK_SIM_CURRENT,
  beds: MOCK_WARD_BEDS,
};

export const MOCK_EMERGENCY_TASK: Task = {
  id: 101,
  patient_id: 12,
  bed: 12,
  type: 'page_doctor',
  title: 'Page the on-duty doctor: Bed 12',
  reason: 'EMERGENCY: Hypotension shock (SBP 78, HR 135, SpO2 86% on air, RR 28)',
  priority: 99.0,
  status: 'active',
  emergency: true,
  escalated: false,
  created_at: '2026-10-20T11:00:00',
  waiting_minutes: 5.0,
};

export const MOCK_ACTIVE_TASKS_WARDPULSE: Task[] = [
  {
    id: 102,
    patient_id: 7,
    bed: 7,
    type: 'page_doctor',
    title: 'Page the on-duty doctor: Bed 7',
    reason: 'RR 14 -> 22 over 5h (+57% baseline breach), HR 98 bpm (post-op trend)',
    priority: 84.5,
    status: 'active',
    emergency: false,
    escalated: true,
    created_at: '2026-10-20T10:15:00',
    waiting_minutes: 50.0,
  },
  {
    id: 103,
    patient_id: 4,
    bed: 4,
    type: 'repeat_bp',
    target_vital: 'sbp',
    title: 'Repeat manual BP: Bed 4',
    reason: 'BP not taken for 7.2h (due interval 4h); borderline tachycardia HR 94',
    priority: 72.0,
    status: 'active',
    emergency: false,
    escalated: false,
    created_at: '2026-10-20T10:45:00',
    waiting_minutes: 20.0,
  },
];

export const MOCK_QUEUE_TASKS_WARDPULSE: Task[] = [
  {
    id: 104,
    patient_id: 8,
    bed: 8,
    type: 'repeat_resp_rate',
    target_vital: 'rr',
    title: 'Recount breathing rate: Bed 8',
    reason: 'Vitals stale by 6.5h; known COPD baseline',
    priority: 45.0,
    status: 'queued',
    emergency: false,
    escalated: false,
    created_at: '2026-10-20T10:50:00',
    waiting_minutes: 15.0,
  },
  {
    id: 105,
    patient_id: 2,
    bed: 2,
    type: 'repeat_heart_rate',
    target_vital: 'hr',
    title: 'Recheck pulse: Bed 2',
    reason: 'Mild pulse fluctuation in post-cardiac observation',
    priority: 38.0,
    status: 'queued',
    emergency: false,
    escalated: false,
    created_at: '2026-10-20T10:55:00',
    waiting_minutes: 10.0,
  },
];

export const MOCK_TASKS_WARDPULSE: TasksResponse = {
  mode: 'wardpulse',
  now: MOCK_SIM_CURRENT,
  budget_k: 2,
  emergency: [MOCK_EMERGENCY_TASK],
  active: MOCK_ACTIVE_TASKS_WARDPULSE,
  queue: MOCK_QUEUE_TASKS_WARDPULSE,
  alerts_shown: 3, // 1 emergency + 2 active
};

export const MOCK_TASKS_NEWS2: TasksResponse = {
  mode: 'news2',
  now: MOCK_SIM_CURRENT,
  budget_k: null,
  emergency: [],
  active: [
    {
      id: 201,
      patient_id: 12,
      bed: 12,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 12',
      reason: 'Aggregate NEWS2 score 12 (Critical risk)',
      priority: 12.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T11:00:00',
      waiting_minutes: 5.0,
    },
    {
      id: 202,
      patient_id: 3,
      bed: 3,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 3',
      reason: 'Breathing rate 22 bpm (Scale 1 standard threshold breach)',
      priority: 6.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T08:00:00',
      waiting_minutes: 185.0,
    },
    {
      id: 203,
      patient_id: 7,
      bed: 7,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 7',
      reason: 'Breathing rate 22 bpm, HR 98 bpm (NEWS2 score 5)',
      priority: 5.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T07:00:00',
      waiting_minutes: 245.0,
    },
    {
      id: 204,
      patient_id: 2,
      bed: 2,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 2',
      reason: 'Aggregate NEWS2 score 5',
      priority: 5.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T09:00:00',
      waiting_minutes: 125.0,
    },
    {
      id: 205,
      patient_id: 4,
      bed: 4,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 4',
      reason: 'Single parameter score 3 on HR',
      priority: 5.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T09:30:00',
      waiting_minutes: 95.0,
    },
    {
      id: 206,
      patient_id: 6,
      bed: 6,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 6',
      reason: 'Aggregate NEWS2 score 6',
      priority: 6.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T08:30:00',
      waiting_minutes: 155.0,
    },
    {
      id: 207,
      patient_id: 8,
      bed: 8,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 8',
      reason: 'Breathing rate 23 bpm, SpO2 91% (NEWS2 score 7)',
      priority: 7.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T07:15:00',
      waiting_minutes: 230.0,
    },
    {
      id: 208,
      patient_id: 15,
      bed: 15,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 15',
      reason: 'Aggregate NEWS2 score 6',
      priority: 6.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T06:40:00',
      waiting_minutes: 265.0,
    },
    {
      id: 209,
      patient_id: 18,
      bed: 18,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 18',
      reason: 'Heart rate 102 bpm (NEWS2 score 5)',
      priority: 5.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T09:10:00',
      waiting_minutes: 115.0,
    },
    {
      id: 210,
      patient_id: 19,
      bed: 19,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 19',
      reason: 'Aggregate NEWS2 score 5',
      priority: 5.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T08:15:00',
      waiting_minutes: 170.0,
    },
    {
      id: 211,
      patient_id: 14,
      bed: 14,
      type: 'news2_alert',
      title: 'Abnormal vitals: Bed 14',
      reason: 'Temp 38.3 C (NEWS2 score 5)',
      priority: 5.0,
      status: 'active',
      emergency: false,
      escalated: false,
      created_at: '2026-10-20T09:50:00',
      waiting_minutes: 75.0,
    },
  ],
  queue: [],
  alerts_shown: 11, // 11 unbudgeted alerts flooding the screen!
};

export const MOCK_SIM_STATE: SimState = {
  running: true,
  speed_minutes_per_second: 10.0,
  sim_time: MOCK_SIM_CURRENT,
  start_time: MOCK_SIM_START,
  scenario: 'default',
};

export function getMockPatientDetail(patientId: number): PatientDetail {
  const patient = MOCK_PATIENTS.find((p) => p.id === patientId) || MOCK_PATIENTS[0];
  const bed = patient.bed;

  // Generate 8 recent vitals readings for sparklines
  const readings: VitalsReading[] = [];
  const baseHr = bed === 12 ? 135 : bed === 7 ? 98 : bed === 3 ? 76 : 72;
  const baseSbp = bed === 12 ? 78 : bed === 4 ? 130 : 120;
  const baseDbp = bed === 12 ? 50 : 80;
  const baseRr = bed === 12 ? 28 : bed === 7 ? 22 : bed === 3 ? 21 : 16;
  const baseSpo2 = bed === 12 ? 86 : bed === 3 ? 91 : 97;
  const baseTemp = 36.8;

  for (let i = 7; i >= 0; i--) {
    const hoursAgo = i * 2;
    const ts = new Date(new Date(MOCK_SIM_CURRENT).getTime() - hoursAgo * 3600000).toISOString();
    readings.push({
      id: 1000 + i,
      patient_id: patientId,
      timestamp: ts,
      source: 'sim',
      hr: Math.round(baseHr + (i > 1 ? -i * 2 : 0)),
      sbp: Math.round(baseSbp + (i > 1 ? i * 4 : 0)),
      dbp: Math.round(baseDbp + (i > 1 ? i * 2 : 0)),
      rr: Math.round(baseRr + (i > 1 && bed === 7 ? -i : 0)),
      spo2: Math.round(baseSpo2 + (i > 1 && bed === 12 ? i * 2 : 0)),
      temp: parseFloat((baseTemp + (i % 2 === 0 ? 0.2 : -0.1)).toFixed(1)),
      on_oxygen: bed === 3 || bed === 12,
      consciousness: bed === 12 && i === 0 ? 'V' : 'A',
    });
  }

  const assessment: PatientAssessment = {
    patient_id: patientId,
    bed: bed,
    risk_score: bed === 12 ? 0.95 : bed === 7 ? 0.72 : bed === 4 ? 0.55 : 0.15,
    risk_tier: bed === 12 ? 'critical' : bed === 7 ? 'high' : bed === 4 ? 'medium' : 'low',
    crash: bed === 12,
    stale_vitals: bed === 4 ? ['sbp', 'dbp'] : [],
    hours_since_last_vitals: bed === 4 ? 7.2 : 0.8,
    next_vitals_due: new Date(new Date(MOCK_SIM_CURRENT).getTime() + 3600000).toISOString(),
    news2_score: bed === 12 ? 12 : bed === 7 ? 5 : bed === 3 ? 3 : 1,
    reasons:
      bed === 12
        ? ['CRASH: Severe hypotension (SBP 78)', 'Tachycardia HR 135', 'Hypoxia SpO2 86%']
        : bed === 7
        ? ['Post-op RR trend +57% above baseline', 'HR 98 elevating', 'High risk tier']
        : bed === 4
        ? ['Blood pressure stale for 7.2 hours', 'Baseline borderline HR 94']
        : ['Vitals within expected individual baseline limits'],
  };

  const openTasks = [
    ...(bed === 12 ? [MOCK_EMERGENCY_TASK] : []),
    ...MOCK_ACTIVE_TASKS_WARDPULSE.filter((t) => t.patient_id === patientId),
    ...MOCK_QUEUE_TASKS_WARDPULSE.filter((t) => t.patient_id === patientId),
  ];

  return {
    patient,
    recent_vitals: readings,
    assessment,
    open_tasks: openTasks,
  };
}
