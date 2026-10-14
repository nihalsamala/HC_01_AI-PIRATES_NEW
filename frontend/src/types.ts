/**
 * WardPulse frontend type definitions.
 * Exactly mirrors backend/shared/schemas.py.
 */

export type Source = 'sim' | 'replay' | 'manual';

export type VitalName = 'hr' | 'sbp' | 'dbp' | 'rr' | 'spo2' | 'temp';

export type Consciousness = 'A' | 'C' | 'V' | 'P' | 'U';

export type Condition = 'copd' | 'post_op' | 'cardiac';

export type RiskTier = 'low' | 'medium' | 'high' | 'critical';

export type WardStatus = 'stable' | 'watch' | 'action' | 'critical';

export type Mode = 'wardpulse' | 'news2';

export type TaskType =
  | 'page_doctor'
  | 'repeat_bp'
  | 'repeat_resp_rate'
  | 'repeat_spo2'
  | 'repeat_heart_rate'
  | 'repeat_temp'
  | 'full_vitals_recheck'
  | 'sit_upright'
  | 'check_oxygen_cannula'
  | 'news2_alert';

export type TaskStatus = 'active' | 'queued' | 'done' | 'dismissed';

export type StreamEventType =
  | 'tasks_updated'
  | 'ward_updated'
  | 'sim_tick'
  | 'emergency';

export const TASK_TITLES: Record<TaskType, string> = {
  page_doctor: 'Page the on-duty doctor: Bed {bed}',
  repeat_bp: 'Repeat manual BP: Bed {bed}',
  repeat_resp_rate: 'Recount breathing rate: Bed {bed}',
  repeat_spo2: 'Recheck oxygen level: Bed {bed}',
  repeat_heart_rate: 'Recheck pulse: Bed {bed}',
  repeat_temp: 'Recheck temperature: Bed {bed}',
  full_vitals_recheck: 'Take a full set of vitals: Bed {bed}',
  sit_upright: 'Sit patient upright to 45 degrees: Bed {bed}',
  check_oxygen_cannula: 'Check oxygen cannula: Bed {bed}',
  news2_alert: 'Abnormal vitals: Bed {bed}',
};

export const TASK_TARGET_VITAL: Partial<Record<TaskType, VitalName>> = {
  repeat_bp: 'sbp',
  repeat_resp_rate: 'rr',
  repeat_spo2: 'spo2',
  repeat_heart_rate: 'hr',
  repeat_temp: 'temp',
};

export interface Patient {
  id: number;
  bed: number;
  age: number;
  conditions: Condition[];
  admitted_at: string;
  display_name?: string | null;
  focus_vitals?: VitalName[];
}

export interface VitalsBase {
  hr?: number | null;
  sbp?: number | null;
  dbp?: number | null;
  rr?: number | null;
  spo2?: number | null;
  temp?: number | null;
  on_oxygen?: boolean;
  consciousness?: Consciousness;
}

export interface VitalsIn extends VitalsBase {
  patient_id: number;
  timestamp?: string | null;
  source?: Source;
}

export interface VitalsReading extends VitalsBase {
  id: number;
  patient_id: number;
  timestamp: string;
  source: Source;
}

export interface PatientAssessment {
  patient_id: number;
  bed: number;
  risk_score: number;
  risk_tier: RiskTier;
  crash: boolean;
  stale_vitals: VitalName[];
  hours_since_last_vitals?: number | null;
  next_vitals_due?: string | null;
  news2_score?: number | null;
  reasons: string[];
}

export interface Task {
  id: number;
  patient_id: number;
  bed: number;
  type: TaskType;
  target_vital?: VitalName | null;
  title: string;
  reason: string;
  priority: number;
  status: TaskStatus;
  emergency: boolean;
  escalated: boolean;
  created_at: string;
  waiting_minutes: number;
  resolved_at?: string | null;
}

export interface TasksResponse {
  mode: Mode;
  now: string;
  budget_k?: number | null;
  emergency: Task[];
  active: Task[];
  queue: Task[];
  alerts_shown: number;
}

export interface WardBed {
  patient_id: number;
  bed: number;
  conditions: Condition[];
  status: WardStatus;
  risk_tier: RiskTier;
  data_stale: boolean;
  hours_since_last_vitals?: number | null;
  has_open_task: boolean;
}

export interface WardOverview {
  now: string;
  beds: WardBed[];
}

export interface WardEvaluation {
  assessments: PatientAssessment[];
  tasks: TasksResponse;
  ward: WardOverview;
}

export interface PatientDetail {
  patient: Patient;
  recent_vitals: VitalsReading[];
  assessment?: PatientAssessment | null;
  open_tasks: Task[];
}

export interface TaskFeedbackIn {
  note?: string | null;
}

export interface AuditEntry {
  id: number;
  timestamp: string;
  event_type: string;
  patient_id?: number | null;
  task_id?: number | null;
  details: Record<string, any>;
}

export interface SimState {
  running: boolean;
  speed_minutes_per_second: number;
  sim_time: string;
  start_time: string;
  scenario: string;
}

export interface SimControl {
  action: 'play' | 'pause' | 'reset' | 'set_speed';
  speed_minutes_per_second?: number | null;
}

export interface StreamEvent {
  type: StreamEventType;
  timestamp: string;
  data: Record<string, any>;
}

export interface SystemMetrics {
  system: Mode;
  events_total: number;
  events_detected: number;
  sensitivity?: number | null;
  median_lead_time_hours?: number | null;
  alerts_per_nurse_hour?: number | null;
  measure_tasks_per_nurse_hour?: number | null;
  false_alert_ratio?: number | null;
}

export interface EvalResults {
  dataset: string;
  sampling_interval_hours: number;
  n_patients: number;
  generated_at: string;
  systems: SystemMetrics[];
  notes: string[];
}
