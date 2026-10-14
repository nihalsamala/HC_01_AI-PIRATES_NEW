import {
  Mode,
  PatientDetail,
  SimControl,
  SimState,
  Task,
  TaskFeedbackIn,
  TasksResponse,
  VitalsIn,
  VitalsReading,
  WardOverview,
  EvalResults,
} from '../types';
import {
  MOCK_PATIENTS,
  MOCK_SIM_STATE,
  MOCK_TASKS_NEWS2,
  MOCK_TASKS_WARDPULSE,
  MOCK_WARD_OVERVIEW,
  getMockPatientDetail,
} from '../mock/mockData';

export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// In-memory mock state for interactive demo without backend
class MockStore {
  simState: SimState = { ...MOCK_SIM_STATE };
  wardPulseTasks: TasksResponse = JSON.parse(JSON.stringify(MOCK_TASKS_WARDPULSE));
  news2Tasks: TasksResponse = JSON.parse(JSON.stringify(MOCK_TASKS_NEWS2));
  wardOverview: WardOverview = JSON.parse(JSON.stringify(MOCK_WARD_OVERVIEW));
  subscribers: Array<() => void> = [];

  subscribe(cb: () => void) {
    this.subscribers.push(cb);
    return () => {
      this.subscribers = this.subscribers.filter((s) => s !== cb);
    };
  }

  notify() {
    this.subscribers.forEach((cb) => cb());
  }

  markDone(taskId: number) {
    const remove = (tasks: Task[]) => tasks.filter((t) => t.id !== taskId);
    this.wardPulseTasks.emergency = remove(this.wardPulseTasks.emergency);
    this.wardPulseTasks.active = remove(this.wardPulseTasks.active);
    this.wardPulseTasks.queue = remove(this.wardPulseTasks.queue);
    this.wardPulseTasks.alerts_shown =
      this.wardPulseTasks.emergency.length + this.wardPulseTasks.active.length;

    this.news2Tasks.active = remove(this.news2Tasks.active);
    this.news2Tasks.alerts_shown = this.news2Tasks.active.length;
    this.notify();
  }

  setMockTime(isoString: string) {
    this.simState.sim_time = isoString;
    this.wardPulseTasks.now = isoString;
    this.news2Tasks.now = isoString;
    this.wardOverview.now = isoString;
    this.notify();
  }

  advanceMockClock() {
    if (!this.simState.running) return;
    const current = new Date(this.simState.sim_time);
    const stepSeconds = (this.simState.speed_minutes_per_second * 60) / 10; // modest advance
    current.setSeconds(current.getSeconds() + stepSeconds);
    this.simState.sim_time = current.toISOString();
    this.wardPulseTasks.now = this.simState.sim_time;
    this.news2Tasks.now = this.simState.sim_time;
    this.wardOverview.now = this.simState.sim_time;
    this.notify();
  }
}

export const mockStore = new MockStore();

// Polling timer for mock live feeling
let mockTimer: number | null = null;
if (USE_MOCK && typeof window !== 'undefined') {
  mockTimer = window.setInterval(() => {
    mockStore.advanceMockClock();
  }, 1000);
}

export async function fetchWard(): Promise<WardOverview> {
  if (USE_MOCK) {
    return Promise.resolve(mockStore.wardOverview);
  }
  const res = await fetch(`${API_URL}/ward`);
  if (!res.ok) throw new Error(`Failed to fetch ward: ${res.statusText}`);
  return res.json();
}

export async function fetchTasks(mode: Mode): Promise<TasksResponse> {
  if (USE_MOCK) {
    return Promise.resolve(
      mode === 'wardpulse' ? mockStore.wardPulseTasks : mockStore.news2Tasks
    );
  }
  const res = await fetch(`${API_URL}/tasks?mode=${mode}`);
  if (!res.ok) throw new Error(`Failed to fetch tasks: ${res.statusText}`);
  return res.json();
}

export async function fetchPatientDetail(patientId: number): Promise<PatientDetail> {
  if (USE_MOCK) {
    return Promise.resolve(getMockPatientDetail(patientId));
  }
  const res = await fetch(`${API_URL}/patients/${patientId}`);
  if (!res.ok) throw new Error(`Failed to fetch patient ${patientId}: ${res.statusText}`);
  return res.json();
}

export async function postVitals(vitals: VitalsIn): Promise<VitalsReading> {
  if (USE_MOCK) {
    // Add reading to mock
    const reading: VitalsReading = {
      ...vitals,
      id: Math.floor(Math.random() * 90000) + 10000,
      patient_id: vitals.patient_id,
      timestamp: vitals.timestamp || mockStore.simState.sim_time,
      source: vitals.source || 'manual',
    };
    mockStore.notify();
    return Promise.resolve(reading);
  }
  const res = await fetch(`${API_URL}/vitals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(vitals),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to submit vitals: ${res.statusText}`);
  }
  return res.json();
}

export async function postTaskDone(taskId: number, feedback?: TaskFeedbackIn): Promise<Task> {
  if (USE_MOCK) {
    mockStore.markDone(taskId);
    return Promise.resolve({} as Task);
  }
  const res = await fetch(`${API_URL}/tasks/${taskId}/done`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(feedback || {}),
  });
  if (!res.ok) throw new Error(`Failed to mark task done: ${res.statusText}`);
  return res.json();
}

export async function postTaskNotUseful(taskId: number, feedback?: TaskFeedbackIn): Promise<Task> {
  if (USE_MOCK) {
    mockStore.markDone(taskId);
    return Promise.resolve({} as Task);
  }
  const res = await fetch(`${API_URL}/tasks/${taskId}/not-useful`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(feedback || {}),
  });
  if (!res.ok) throw new Error(`Failed to dismiss task: ${res.statusText}`);
  return res.json();
}

export async function fetchSimState(): Promise<SimState> {
  if (USE_MOCK) {
    return Promise.resolve(mockStore.simState);
  }
  const res = await fetch(`${API_URL}/sim/state`);
  if (!res.ok) throw new Error(`Failed to fetch sim state: ${res.statusText}`);
  return res.json();
}

export async function controlSim(control: SimControl): Promise<SimState> {
  if (USE_MOCK) {
    if (control.action === 'play') mockStore.simState.running = true;
    if (control.action === 'pause') mockStore.simState.running = false;
    if (control.action === 'reset') {
      mockStore.simState = { ...MOCK_SIM_STATE, sim_time: MOCK_SIM_STATE.start_time };
      mockStore.wardPulseTasks = JSON.parse(JSON.stringify(MOCK_TASKS_WARDPULSE));
      mockStore.news2Tasks = JSON.parse(JSON.stringify(MOCK_TASKS_NEWS2));
      mockStore.wardOverview = JSON.parse(JSON.stringify(MOCK_WARD_OVERVIEW));
    }
    if (control.action === 'set_speed' && control.speed_minutes_per_second !== undefined) {
      mockStore.simState.speed_minutes_per_second = control.speed_minutes_per_second || 10.0;
    }
    mockStore.notify();
    return Promise.resolve(mockStore.simState);
  }
  const res = await fetch(`${API_URL}/sim/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(control),
  });
  if (!res.ok) throw new Error(`Failed to control sim: ${res.statusText}`);
  return res.json();
}

export async function fetchEvalResults(): Promise<EvalResults | null> {
  if (USE_MOCK) {
    return Promise.resolve(null);
  }
  try {
    const res = await fetch(`${API_URL}/eval/results`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

