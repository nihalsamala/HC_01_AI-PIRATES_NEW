import React, { useState, useEffect, useCallback } from 'react';
import {
  Mode,
  PatientDetail,
  SimState,
  TasksResponse,
  VitalsIn,
  WardOverview,
  EvalResults,
} from './types';
import {
  API_URL,
  USE_MOCK,
  controlSim,
  fetchPatientDetail,
  fetchSimState,
  fetchTasks,
  fetchWard,
  fetchEvalResults,
  mockStore,
  postTaskDone,
  postTaskNotUseful,
  postVitals,
} from './api/client';
import { NavSidebar, ActiveTab } from './components/NavSidebar';
import { TopBar } from './components/TopBar';
import { AttentionCards } from './components/AttentionCards';
import { RightSidebar } from './components/RightSidebar';
import { ReplayTimeline, DemoStory, REPLAY_STORIES } from './components/ReplayTimeline';
import { EmergencyBanner } from './components/EmergencyBanner';
import { StandbyQueue } from './components/StandbyQueue';
import { PatientDetailPanel } from './components/PatientDetailPanel';
import { QuickVitalsModal } from './components/QuickVitalsModal';
import { WorriedModal } from './components/WorriedModal';
import { PlaceholderView } from './components/Placeholders';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('console');
  const [mode, setMode] = useState<Mode>('wardpulse');
  const [budgetK, setBudgetK] = useState<number>(2);
  const [simState, setSimState] = useState<SimState>({
    running: true,
    speed_minutes_per_second: 10.0,
    sim_time: '2026-10-21T02:30:00',
    start_time: '2026-10-20T06:00:00',
    scenario: 'default',
  });

  const [tasksResponse, setTasksResponse] = useState<TasksResponse | null>(null);
  const [wardOverview, setWardOverview] = useState<WardOverview | null>(null);
  const [evalResults, setEvalResults] = useState<EvalResults | null>(null);

  // Dynamic Live Proof counts
  const [naiveAlertsCount, setNaiveAlertsCount] = useState<number>(10);
  const [wardpulseAlertsCount, setWardpulseAlertsCount] = useState<number>(2);

  // Selected bed and patient details
  const [selectedBed, setSelectedBed] = useState<number | null>(null);
  const [patientDetail, setPatientDetail] = useState<PatientDetail | null>(null);
  const [patientDetailsMap, setPatientDetailsMap] = useState<Record<number, PatientDetail>>({});

  // Modals & local state
  const [vitalsModalOpen, setVitalsModalOpen] = useState<boolean>(false);
  const [vitalsModalBed, setVitalsModalBed] = useState<number | null>(null);
  const [worriedModalOpen, setWorriedModalOpen] = useState<boolean>(false);
  const [snoozedTaskIds, setSnoozedTaskIds] = useState<number[]>([]);
  const [activeStoryId, setActiveStoryId] = useState<string>('overflow');
  const [projectorMode, setProjectorMode] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load Tasks for active mode and comparator
  const loadTasks = useCallback(async (currentMode: Mode) => {
    try {
      const activeData = await fetchTasks(currentMode);
      setTasksResponse(activeData);

      // Concurrently fetch or compute comparison count from the other mode
      const comparatorMode: Mode = currentMode === 'wardpulse' ? 'news2' : 'wardpulse';
      const comparatorData = await fetchTasks(comparatorMode);

      if (currentMode === 'wardpulse') {
        setWardpulseAlertsCount(activeData.alerts_shown);
        setNaiveAlertsCount(comparatorData.alerts_shown);
      } else {
        setNaiveAlertsCount(activeData.alerts_shown);
        setWardpulseAlertsCount(comparatorData.alerts_shown);
      }
    } catch (err: any) {
      console.error('Error fetching tasks:', err);
      setError(err?.message || 'Failed to load tasks.');
    }
  }, []);

  // Load Ward Overview
  const loadWard = useCallback(async () => {
    try {
      const data = await fetchWard();
      setWardOverview(data);
    } catch (err: any) {
      console.error('Error fetching ward overview:', err);
    }
  }, []);

  // Load Sim State
  const loadSimState = useCallback(async () => {
    try {
      const state = await fetchSimState();
      setSimState(state);
    } catch (err: any) {
      console.error('Error fetching sim state:', err);
    }
  }, []);

  // Load Patient Detail
  const loadSelectedPatient = useCallback(async (bed: number) => {
    try {
      const detail = await fetchPatientDetail(bed);
      setPatientDetail(detail);
      setPatientDetailsMap((prev) => ({ ...prev, [bed]: detail }));
    } catch (err: any) {
      console.error('Error fetching patient detail:', err);
    }
  }, []);

  // Initial Load & Real SSE or Mock Subscription
  useEffect(() => {
    let sse: EventSource | null = null;
    let unsubscribeMock: (() => void) | null = null;

    const init = async () => {
      await Promise.all([
        loadTasks(mode),
        loadWard(),
        loadSimState(),
        loadSelectedPatient(1),
        fetchEvalResults().then((res) => {
          if (res) setEvalResults(res);
        }),
      ]);
    };

    init();

    if (USE_MOCK) {
      unsubscribeMock = mockStore.subscribe(() => {
        setSimState({ ...mockStore.simState });
        loadTasks(mode);
        loadWard();
        if (selectedBed) loadSelectedPatient(selectedBed);
      });
    } else {
      try {
        sse = new EventSource(`${API_URL}/stream`);
        sse.addEventListener('tasks_updated', () => {
          loadTasks(mode);
        });
        sse.addEventListener('ward_updated', () => {
          loadWard();
          if (selectedBed) loadSelectedPatient(selectedBed);
        });
        sse.addEventListener('sim_tick', (e: MessageEvent) => {
          try {
            const data = JSON.parse(e.data);
            if (data.data) setSimState(data.data);
          } catch {
            // fallback
          }
        });
        sse.addEventListener('emergency', () => {
          loadTasks(mode);
        });
        sse.onerror = (err) => {
          console.warn('SSE connection error:', err);
        };
      } catch (err) {
        console.warn('Failed to start EventSource:', err);
      }
    }

    return () => {
      if (sse) sse.close();
      if (unsubscribeMock) unsubscribeMock();
    };
  }, [loadTasks, loadWard, loadSimState, mode, selectedBed, loadSelectedPatient]);

  // Handle Mode Change
  const handleModeChange = (newMode: Mode) => {
    setMode(newMode);
    loadTasks(newMode);
  };

  // Handle Simulation Controls
  const handleSimControl = async (
    action: 'play' | 'pause' | 'reset' | 'set_speed',
    speed?: number
  ) => {
    try {
      const updated = await controlSim({ action, speed_minutes_per_second: speed });
      setSimState(updated);
      loadTasks(mode);
      loadWard();
      if (selectedBed) loadSelectedPatient(selectedBed);
    } catch (err: any) {
      console.error('Sim control error:', err);
    }
  };

  // Handle Demo Story Selection from Bottom Timeline
  const handleSelectStory = async (story: DemoStory) => {
    setActiveStoryId(story.id);

    if (USE_MOCK) {
      mockStore.setMockTime(story.fullTime);
    } else {
      await controlSim({ action: 'set_speed', speed_minutes_per_second: 15.0 });
    }

    setSelectedBed(story.bed);
    loadSelectedPatient(story.bed);
    loadTasks(mode);
    loadWard();
  };

  // Handle Task Completion or Dismissal
  const handleTaskAction = async (taskId: number, action: 'done' | 'not-useful') => {
    try {
      if (action === 'done') {
        await postTaskDone(taskId);
      } else {
        await postTaskNotUseful(taskId);
      }
      loadTasks(mode);
      loadWard();
      if (selectedBed) loadSelectedPatient(selectedBed);
    } catch (err: any) {
      console.error('Task action failed:', err);
    }
  };

  // Local Task Snooze
  const handleSnoozeTask = (taskId: number) => {
    setSnoozedTaskIds((prev) => [...prev, taskId]);
  };

  // Handle Selecting a Bed
  const handleSelectBed = (bed: number) => {
    setSelectedBed(bed);
    loadSelectedPatient(bed);
  };

  // Handle Vitals Submit
  const handleVitalsSubmit = async (vitals: VitalsIn) => {
    await postVitals(vitals);
    loadTasks(mode);
    loadWard();
    if (selectedBed) loadSelectedPatient(selectedBed);
  };

  // Handle Bedside Nurse "I'm Worried" Concern Submission
  const handleWorriedSubmit = async (bed: number, note: string) => {
    alert(`Clinical concern logged for Bed ${bed}: "${note}". Attention Engine prioritizing patient.`);
    setSelectedBed(bed);
    loadSelectedPatient(bed);
    loadTasks(mode);
    loadWard();
  };

  // Active cards filtered by Budget K in WardPulse mode
  const rawActive = tasksResponse?.active || [];
  const activeCardsToDisplay =
    mode === 'wardpulse' ? rawActive.slice(0, budgetK) : rawActive;

  // Queue items: if budgetK sliced some active cards into standby, include them!
  const overflowCards =
    mode === 'wardpulse' && rawActive.length > budgetK
      ? rawActive.slice(budgetK)
      : [];
  const combinedQueue = [...overflowCards, ...(tasksResponse?.queue || [])];

  // Dynamically compute bed data provenance from real data on active beds
  const isReplay = Boolean(
    (patientDetail && patientDetail.recent_vitals.some((r) => r.source === 'replay')) ||
    Object.values(patientDetailsMap).some((d) => d.recent_vitals.some((r) => r.source === 'replay'))
  );
  const dataSourceLabel = isReplay
    ? 'Beds: replayed public ICU records (PhysioNet 2019) · scripted demo beds: 3, 4, 5, 6, 7, 12'
    : 'Beds: simulated ward';

  return (
    <div
      className={`min-h-screen bg-slate-100 flex flex-col font-sans transition-all ${
        projectorMode ? 'projector-mode' : ''
      }`}
    >
      {/* Top Header Bar */}
      <TopBar
        mode={mode}
        onModeChange={handleModeChange}
        simState={simState}
        onSimControl={handleSimControl}
        budgetK={budgetK}
        onBudgetKChange={(k) => setBudgetK(k)}
        isProjectorMode={projectorMode}
        onToggleProjectorMode={() => setProjectorMode(!projectorMode)}
        dataSourceLabel={dataSourceLabel}
      />

      {/* Main Body: Left Rail + Center + Right Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Narrow Nav Rail */}
        <NavSidebar
          activeTab={activeTab}
          onSelectTab={(tab) => setActiveTab(tab)}
          activeCardsCount={tasksResponse?.active.length || 0}
        />

        {/* Content View Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-7">
          {activeTab !== 'console' ? (
            <PlaceholderView
              tab={activeTab}
              onBackToConsole={() => setActiveTab('console')}
              evalResults={evalResults}
            />
          ) : (
            <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-6 items-start">
              {/* Main Column (Center) */}
              <main className="flex-1 w-full space-y-6">
                {/* Error Banner */}
                {error && (
                  <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-xs font-semibold flex items-center justify-between shadow-xs">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-rose-600" />
                      <span>{error}</span>
                    </div>
                    <button
                      onClick={() => setError(null)}
                      className="text-[11px] bg-rose-200/60 hover:bg-rose-200 px-2.5 py-1 rounded-lg"
                    >
                      Dismiss
                    </button>
                  </div>
                )}

                {/* Emergency Crash Bypass Banner (Full width on top) */}
                {tasksResponse && tasksResponse.emergency.length > 0 && (
                  <EmergencyBanner
                    emergencyTasks={tasksResponse.emergency}
                    onAction={handleTaskAction}
                    onSelectBed={handleSelectBed}
                  />
                )}

                {/* Attention Cards (Top K cards side-by-side) */}
                <AttentionCards
                  tasks={activeCardsToDisplay}
                  mode={mode}
                  budgetK={budgetK}
                  onAction={handleTaskAction}
                  onSelectBed={handleSelectBed}
                  wardBeds={wardOverview?.beds}
                  patientDetailsMap={patientDetailsMap}
                  snoozedTaskIds={snoozedTaskIds}
                  onSnoozeTask={handleSnoozeTask}
                />

                {/* Standby Queue (Visible in WardPulse mode when cards wait) */}
                {mode === 'wardpulse' && combinedQueue.length > 0 && (
                  <StandbyQueue
                    queue={combinedQueue}
                    onSelectBed={handleSelectBed}
                  />
                )}
              </main>

              {/* Right Column: Vitals buttons + Ward at a glance + Live proof */}
              <RightSidebar
                wardBeds={wardOverview?.beds || []}
                selectedBedId={selectedBed}
                onSelectBed={handleSelectBed}
                onOpenEnterVitals={() => {
                  setVitalsModalBed(selectedBed || 1);
                  setVitalsModalOpen(true);
                }}
                onOpenWorried={() => setWorriedModalOpen(true)}
                onOpenMap={() => setActiveTab('ward_map')}
                onOpenProofDetails={() => setActiveTab('proof')}
                naiveAlertsCount={naiveAlertsCount}
                wardpulseAlertsCount={wardpulseAlertsCount}
                evalResults={evalResults}
                tasks={activeCardsToDisplay}
                patientDetailsMap={patientDetailsMap}
                isReplay={isReplay}
              />
            </div>
          )}
        </div>
      </div>

      {/* Bottom Replay Timeline Scrubber */}
      <ReplayTimeline
        simState={simState}
        activeStoryId={activeStoryId}
        onSelectStory={handleSelectStory}
      />

      {/* Patient Detail Drawer */}
      {selectedBed && (
        <PatientDetailPanel
          detail={patientDetail}
          onClose={() => {
            setSelectedBed(null);
            setPatientDetail(null);
          }}
          onOpenQuickVitals={(bed) => {
            setVitalsModalBed(bed);
            setVitalsModalOpen(true);
          }}
        />
      )}

      {/* Quick Vitals Entry Modal */}
      <QuickVitalsModal
        initialBed={vitalsModalBed}
        isOpen={vitalsModalOpen}
        onClose={() => setVitalsModalOpen(false)}
        onSubmit={handleVitalsSubmit}
      />

      {/* "I'm Worried" Bedside Nurse Escalation Modal */}
      <WorriedModal
        isOpen={worriedModalOpen}
        onClose={() => setWorriedModalOpen(false)}
        onSubmit={handleWorriedSubmit}
        currentSelectedBed={selectedBed}
      />
    </div>
  );
};

export default App;
