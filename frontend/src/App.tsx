import React, { useState, useEffect, useCallback } from 'react';
import {
  Mode,
  PatientDetail,
  SimState,
  TasksResponse,
  VitalsIn,
  WardOverview,
} from './types';
import {
  API_URL,
  USE_MOCK,
  controlSim,
  fetchPatientDetail,
  fetchSimState,
  fetchTasks,
  fetchWard,
  mockStore,
  postTaskDone,
  postTaskNotUseful,
  postVitals,
} from './api/client';
import { Header } from './components/Header';
import { ModeToggle } from './components/ModeToggle';
import { DemoBanner, DEMO_STORIES } from './components/DemoBanner';
import { EmergencyBanner } from './components/EmergencyBanner';
import { ActiveCards } from './components/ActiveCards';
import { StandbyQueue } from './components/StandbyQueue';
import { WardStrip } from './components/WardStrip';
import { PatientDetailPanel } from './components/PatientDetailPanel';
import { QuickVitalsModal } from './components/QuickVitalsModal';
import { HelpModal } from './components/HelpModal';
import { PlusCircle, RefreshCw, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [mode, setMode] = useState<Mode>('wardpulse');
  const [simState, setSimState] = useState<SimState>({
    running: true,
    speed_minutes_per_second: 10.0,
    sim_time: '2026-10-20T11:05:00',
    start_time: '2026-10-20T06:00:00',
    scenario: 'default',
  });
  const [tasksResponse, setTasksResponse] = useState<TasksResponse | null>(null);
  const [wardOverview, setWardOverview] = useState<WardOverview | null>(null);
  const [selectedBed, setSelectedBed] = useState<number | null>(null);
  const [patientDetail, setPatientDetail] = useState<PatientDetail | null>(null);
  const [vitalsModalOpen, setVitalsModalOpen] = useState<boolean>(false);
  const [vitalsModalBed, setVitalsModalBed] = useState<number | null>(null);
  const [helpOpen, setHelpOpen] = useState<boolean>(false);
  const [projectorMode, setProjectorMode] = useState<boolean>(false);
  const [demoModeActive, setDemoModeActive] = useState<boolean>(false);
  const [currentStoryIndex, setCurrentStoryIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load Tasks
  const loadTasks = useCallback(async (currentMode: Mode) => {
    try {
      const data = await fetchTasks(currentMode);
      setTasksResponse(data);
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

  // Load Patient Detail if a bed is selected
  const loadSelectedPatient = useCallback(async (bed: number) => {
    try {
      const detail = await fetchPatientDetail(bed);
      setPatientDetail(detail);
    } catch (err: any) {
      console.error('Error fetching patient detail:', err);
    }
  }, []);

  // Initial Load & Real SSE or Mock Subscription
  useEffect(() => {
    let sse: EventSource | null = null;
    let unsubscribeMock: (() => void) | null = null;

    const init = async () => {
      setLoading(true);
      await Promise.all([loadTasks(mode), loadWard(), loadSimState()]);
      setLoading(false);
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

  // Launch Guided Demo Mode
  const handleStartDemo = () => {
    setDemoModeActive(true);
    handleSelectStory(0);
  };

  // Handle Story Selection in Demo Mode
  const handleSelectStory = async (index: number) => {
    setCurrentStoryIndex(index);
    const story = DEMO_STORIES[index];

    if (USE_MOCK) {
      mockStore.setMockTime(story.time);
    } else {
      // In live backend mode, ensure sim speed is optimal for viewing
      await controlSim({ action: 'set_speed', speed_minutes_per_second: 15.0 });
    }

    // Inspect relevant patient bed for clear clinical demonstration
    setSelectedBed(story.highlightBed);
    loadSelectedPatient(story.highlightBed);
    loadTasks(mode);
    loadWard();
  };

  // Handle Task Action (Done / Not Useful)
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

  // Handle Selecting a Bed
  const handleSelectBed = (bed: number) => {
    setSelectedBed(bed);
    loadSelectedPatient(bed);
  };

  // Handle Submitting Quick Vitals
  const handleVitalsSubmit = async (vitals: VitalsIn) => {
    await postVitals(vitals);
    loadTasks(mode);
    loadWard();
    if (selectedBed) loadSelectedPatient(selectedBed);
  };

  return (
    <div className={`min-h-screen bg-slate-100 flex flex-col font-sans transition-all ${projectorMode ? 'projector-mode' : ''}`}>
      {/* Top Header */}
      <Header
        simState={simState}
        onControl={handleSimControl}
        onOpenHelp={() => setHelpOpen(true)}
        onStartDemo={handleStartDemo}
        isProjectorMode={projectorMode}
        onToggleProjectorMode={() => setProjectorMode(!projectorMode)}
      />

      {/* Main Ward Console Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">
        {/* Error message banner */}
        {error && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-sm font-semibold flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-rose-600" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-xs bg-rose-200/60 hover:bg-rose-200 px-3 py-1 rounded-lg"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Guided Demo Story Banner */}
        {demoModeActive && (
          <DemoBanner
            currentStoryIndex={currentStoryIndex}
            onSelectStory={handleSelectStory}
            onCloseDemo={() => setDemoModeActive(false)}
            onSelectBed={handleSelectBed}
          />
        )}

        {/* Mode Toggle & Alert Reduction Counter */}
        <ModeToggle
          mode={mode}
          alertsShown={tasksResponse?.alerts_shown ?? 0}
          onModeChange={handleModeChange}
        />

        {/* Emergency Banner (Full width on top) */}
        {tasksResponse && tasksResponse.emergency.length > 0 && (
          <EmergencyBanner
            emergencyTasks={tasksResponse.emergency}
            onAction={handleTaskAction}
            onSelectBed={handleSelectBed}
          />
        )}

        {/* Active Cards Section (Budgeted Top 2) */}
        <div className="space-y-4">
          <ActiveCards
            tasks={tasksResponse?.active || []}
            mode={mode}
            budgetK={tasksResponse?.budget_k}
            onAction={handleTaskAction}
            onSelectBed={handleSelectBed}
          />
        </div>

        {/* Standby Queue (Only in WardPulse mode when queue exists) */}
        {mode === 'wardpulse' && tasksResponse && tasksResponse.queue.length > 0 && (
          <StandbyQueue
            queue={tasksResponse.queue}
            onSelectBed={handleSelectBed}
          />
        )}

        {/* 20-Bed Ward Overview Strip */}
        <div className="pt-2">
          <WardStrip
            beds={wardOverview?.beds || []}
            selectedBedId={selectedBed}
            onSelectBed={handleSelectBed}
          />
        </div>

        {/* Quick Action Bar */}
        <div className="flex justify-between items-center pt-2">
          <div className="text-xs text-slate-500 font-medium">
            WardPulse Attention Engine • <span className="text-teal-700 font-semibold">20-Bed Medical Ward</span>
          </div>
          <button
            onClick={() => {
              setVitalsModalBed(selectedBed || 1);
              setVitalsModalOpen(true);
            }}
            className="px-5 py-3 rounded-2xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-lg flex items-center gap-2 transition hover:shadow-xl active:scale-95"
          >
            <PlusCircle className="w-4 h-4 text-teal-400" />
            <span>Record New Vitals (Any Bed)</span>
          </button>
        </div>
      </main>

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

      {/* Clinical Help & Rationale Modal */}
      <HelpModal isOpen={helpOpen} onClose={() => setHelpOpen(false)} />
    </div>
  );
};

export default App;
