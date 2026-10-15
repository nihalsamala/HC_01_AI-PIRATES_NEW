import React, { useState } from 'react';
import {
  PhoneCall,
  CheckCircle2,
  BellOff,
  Stethoscope,
  ChevronDown,
  ArrowUp,
  ArrowDown,
  AlertTriangle,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Mode, Task, WardBed, PatientDetail } from '../types';
import { formatCardReason } from '../utils/reasons';

interface AttentionCardsProps {
  tasks: Task[];
  mode: Mode;
  budgetK?: number | null;
  onAction: (taskId: number, action: 'done' | 'not-useful') => void;
  onSelectBed: (bed: number) => void;
  wardBeds?: WardBed[];
  patientDetailsMap?: Record<number, PatientDetail>;
  snoozedTaskIds: number[];
  onSnoozeTask: (taskId: number) => void;
  simTime?: string;
}

interface ParsedVital {
  name: string;
  value: string;
  baseline?: string;
  trend?: 'up' | 'down' | 'neutral';
  staleMinutes?: number;
}

interface ActionStep {
  text: string;
  code: string;
}

// Closed-set action protocol mappings with clinical action codes
const getActionSteps = (task: Task): ActionStep[] => {
  const steps: ActionStep[] = [];
  const text = (task.title || '').replace(`: Bed ${task.bed}`, '');

  if (task.type === 'sit_upright') {
    steps.push({ text: 'Sit patient upright to 45°', code: 'A01' });
    if (task.reason.toLowerCase().includes('temp') || task.reason.toLowerCase().includes('pulse')) {
      steps.push({ text: 'Check temperature and look for rigors', code: 'A05' });
    } else {
      steps.push({ text: 'Recheck breathing rate in 10 minutes', code: 'A03' });
    }
    if (task.escalated || task.priority > 0.7) {
      steps.push({ text: 'Page on-duty doctor (SBAR ready)', code: 'A09' });
    }
  } else if (task.type === 'check_oxygen_cannula') {
    steps.push({ text: 'Check oxygen cannula, mask and flow rate', code: 'A02' });
    steps.push({ text: 'Sit patient upright to 45°', code: 'A01' });
    steps.push({ text: 'Increase observation frequency to hourly', code: 'A08' });
  } else if (task.type === 'page_doctor') {
    steps.push({ text: 'Page on-duty doctor (SBAR ready)', code: 'A09' });
    steps.push({ text: 'Take full set of vitals while waiting', code: 'A08' });
    steps.push({ text: 'Ensure IV access is patent and secure', code: 'A10' });
  } else if (task.type === 'repeat_resp_rate') {
    steps.push({ text: 'Recount breathing rate manually for full 60 seconds', code: 'A03' });
    steps.push({ text: 'Check chest rise and use of accessory muscles', code: 'A01' });
  } else if (task.type === 'repeat_spo2') {
    steps.push({ text: 'Check probe placement and recheck oxygen saturation', code: 'A04' });
    steps.push({ text: 'Check oxygen delivery equipment and flow', code: 'A02' });
  } else if (task.type === 'repeat_bp') {
    steps.push({ text: 'Repeat manual blood pressure with proper cuff size', code: 'A07' });
    steps.push({ text: 'Check patient position and limb perfusion', code: 'A08' });
  } else if (task.type === 'repeat_temp') {
    steps.push({ text: 'Recheck core temperature and observe for rigors', code: 'A05' });
    steps.push({ text: 'Inspect surgical wound or catheter sites if present', code: 'A11' });
  } else if (task.type === 'repeat_heart_rate') {
    steps.push({ text: 'Recheck radial pulse and rhythm manually', code: 'A06' });
    steps.push({ text: 'Compare with baseline and monitor rhythm', code: 'A08' });
  } else if (task.type === 'full_vitals_recheck') {
    steps.push({ text: 'Record complete set of all 6 vital signs', code: 'A08' });
    steps.push({ text: 'Review trends and calculate personal risk score', code: 'A12' });
  } else {
    // news2_alert or default
    steps.push({ text: text || 'Assess patient and verify vitals', code: 'N01' });
    if (task.priority > 0.6 || task.escalated) {
      steps.push({ text: 'Notify charge nurse / medical officer', code: 'A09' });
    }
  }

  return steps;
};

// Helper to extract vital metrics and baseline if present in reason string or detail
const parseVitalsFromTask = (task: Task, patientDetail?: PatientDetail): ParsedVital[] => {
  const vitals: ParsedVital[] = [];
  const reason = task.reason || '';

  // 1. Try regex extraction of "HR 108 (base 78)" or "RR 14 -> 20" from reason string
  const hrMatch = reason.match(/HR\s+(\d+)(?:\s*\((?:base\s+)?(\d+)\))?/i);
  if (hrMatch) {
    const val = hrMatch[1];
    const base = hrMatch[2];
    vitals.push({
      name: 'HR',
      value: val,
      baseline: base,
      trend: base ? (parseInt(val) > parseInt(base) ? 'up' : 'down') : 'up',
      staleMinutes: 22,
    });
  }

  const tempMatch = reason.match(/Temp\s+([0-9.]+)(?:\s*\((?:base\s+)?([0-9.]+)\))?/i);
  if (tempMatch) {
    const val = tempMatch[1];
    const base = tempMatch[2];
    vitals.push({
      name: 'Temp',
      value: `${val}°`,
      baseline: base ? `${base}°` : undefined,
      trend: base ? (parseFloat(val) > parseFloat(base) ? 'up' : 'down') : 'up',
      staleMinutes: 22,
    });
  }

  const rrMatch = reason.match(/RR\s+(\d+)(?:\s*(?:->|\(base\s+)?\s*(\d+)\)?)?/i);
  if (rrMatch) {
    const first = rrMatch[1];
    const second = rrMatch[2];
    let val = first;
    let base = second;
    // In "14 -> 20", 14 was base, 20 is current
    if (reason.includes('->') && second) {
      base = first;
      val = second;
    }
    vitals.push({
      name: 'RR',
      value: val,
      baseline: base,
      trend: base ? (parseInt(val) > parseInt(base) ? 'up' : 'down') : 'up',
      staleMinutes: 30,
    });
  }

  const spo2Match = reason.match(/SpO2\s+(\d+)(?:\s*\((?:base\s+)?(\d+)\))?/i);
  if (spo2Match) {
    const val = spo2Match[1];
    const base = spo2Match[2];
    vitals.push({
      name: 'SpO2',
      value: `${val}%`,
      baseline: base ? `${base}%` : undefined,
      trend: base ? (parseInt(val) > parseInt(base) ? 'up' : 'down') : 'down',
      staleMinutes: 22,
    });
  }

  const bpMatch = reason.match(/BP\s+(\d+\/\d+)(?:\s*\((?:base\s+)?(\d+\/\d+)\))?/i);
  if (bpMatch) {
    const val = bpMatch[1];
    const base = bpMatch[2];
    vitals.push({
      name: 'BP',
      value: val,
      baseline: base,
      trend: 'down',
      staleMinutes: 22,
    });
  }

  // If no vitals parsed from reason but recent readings exist from API
  if (vitals.length === 0 && patientDetail && patientDetail.recent_vitals.length > 0) {
    const latest = patientDetail.recent_vitals[patientDetail.recent_vitals.length - 1];
    if (latest.hr !== null && latest.hr !== undefined) {
      vitals.push({ name: 'HR', value: `${latest.hr}`, staleMinutes: 15 });
    }
    if (latest.spo2 !== null && latest.spo2 !== undefined) {
      vitals.push({ name: 'SpO2', value: `${latest.spo2}%`, staleMinutes: 15 });
    }
    if (latest.rr !== null && latest.rr !== undefined) {
      vitals.push({ name: 'RR', value: `${latest.rr}`, staleMinutes: 15 });
    }
    if (latest.sbp !== null && latest.dbp !== null && latest.sbp !== undefined) {
      vitals.push({ name: 'BP', value: `${latest.sbp}/${latest.dbp}`, staleMinutes: 15 });
    }
  }

  return vitals;
};

// Formats patient label like "Bed 7 · Post-op · 28 M" (anonymous, no real names per Rule 1)
const getPatientLabel = (bedNum: number, wardBed?: WardBed, detail?: PatientDetail): string => {
  let label = `Bed ${bedNum}`;

  if (wardBed && wardBed.conditions && wardBed.conditions.length > 0) {
    const condStr = wardBed.conditions
      .map((c) => (c === 'post_op' ? 'Post-op' : c.toUpperCase()))
      .join(', ');
    label += ` · ${condStr}`;
  } else if (detail && detail.patient.conditions.length > 0) {
    const condStr = detail.patient.conditions
      .map((c) => (c === 'post_op' ? 'Post-op' : c.toUpperCase()))
      .join(', ');
    label += ` · ${condStr}`;
  }

  if (detail && detail.patient.age) {
    label += ` · ${detail.patient.age} y/o`;
  }

  return label;
};

// Compute dynamic vital age chips from actual readings or wardBed data
const getVitalsAgeChips = (detail?: PatientDetail, simTimeStr?: string, wardBed?: WardBed) => {
  const simTime = simTimeStr ? new Date(simTimeStr).getTime() : Date.now();
  const vitals = detail?.recent_vitals || [];

  const getLatestAge = (vitalKey: 'hr' | 'sbp' | 'rr' | 'spo2' | 'temp') => {
    for (let i = vitals.length - 1; i >= 0; i--) {
      const r = vitals[i];
      if (r[vitalKey] !== null && r[vitalKey] !== undefined) {
        const readTime = new Date(r.timestamp).getTime();
        const diffMin = Math.max(0, Math.round((simTime - readTime) / 60000));
        let ageLabel = `${diffMin} min`;
        let status: 'fresh' | 'due' | 'stale' = 'fresh';
        if (diffMin >= 60) {
          ageLabel = `${(diffMin / 60).toFixed(1)}h`;
        }
        if (diffMin > 360) status = 'stale';
        else if (diffMin > 240) status = 'due';
        return { age: ageLabel, status };
      }
    }
    // Fallback if vital not yet loaded: check wardBed overall hours
    if (wardBed && wardBed.hours_since_last_vitals !== null && wardBed.hours_since_last_vitals !== undefined) {
      const h = wardBed.hours_since_last_vitals;
      const status: 'fresh' | 'due' | 'stale' = h > 6 ? 'stale' : (h > 4 ? 'due' : 'fresh');
      return { age: `${h.toFixed(1)}h`, status };
    }
    return { age: 'due', status: 'due' as const };
  };

  return [
    { name: 'HR', ...getLatestAge('hr') },
    { name: 'BP', ...getLatestAge('sbp') },
    { name: 'RR', ...getLatestAge('rr') },
    { name: 'SpO2', ...getLatestAge('spo2') },
    { name: 'Temp', ...getLatestAge('temp') },
  ];
};

export const AttentionCards: React.FC<AttentionCardsProps> = ({
  tasks,
  mode,
  budgetK = 2,
  onAction,
  onSelectBed,
  wardBeds = [],
  patientDetailsMap = {},
  snoozedTaskIds,
  onSnoozeTask,
  simTime,
}) => {
  const [snoozeMenuOpen, setSnoozeMenuOpen] = useState<number | null>(null);
  const [completingTaskId, setCompletingTaskId] = useState<number | null>(null);

  const handleDone = (taskId: number) => {
    setCompletingTaskId(taskId);
    onAction(taskId, 'done');
    setTimeout(() => setCompletingTaskId(null), 800);
  };

  // Filter out snoozed tasks
  const visibleTasks = tasks.filter((t) => !snoozedTaskIds.includes(t.id));

  // Determine active count vs budget K
  const currentBudgetK = budgetK ?? 2;
  const activeCount = visibleTasks.length;

  return (
    <section className="space-y-4">
      {/* Main Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight leading-tight">
            Your next 15 minutes
          </h1>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            {mode === 'wardpulse'
              ? `At most ${currentBudgetK} cards. Everything else is ranked in the queue — nothing is hidden.`
              : 'Showing all unconstrained threshold alerts (Naïve comparator mode).'}
          </p>
        </div>

        {/* Attention Budget Indicator (e.g. 2/2) */}
        {mode === 'wardpulse' && (
          <div className="inline-flex items-center gap-2.5 bg-white border border-slate-200/90 px-3.5 py-1.5 rounded-2xl shadow-xs self-start sm:self-auto">
            <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-500">
              Attention Budget
            </span>

            {/* Visual Budget Bars */}
            <div className="flex items-center gap-1">
              {Array.from({ length: currentBudgetK }).map((_, i) => (
                <div
                  key={i}
                  className={`w-4 h-2 rounded-xs transition-colors ${
                    i < activeCount ? 'bg-teal-600' : 'bg-slate-200'
                  }`}
                />
              ))}
            </div>

            <span className="font-mono text-xs font-black text-slate-800">
              {activeCount}/{currentBudgetK}
            </span>
          </div>
        )}
      </div>

      {/* Empty State */}
      {visibleTasks.length === 0 && (
        <div className="bg-white rounded-3xl border border-dashed border-slate-300 p-8 text-center shadow-xs">
          <div className="w-12 h-12 bg-teal-50 text-teal-700 rounded-2xl mx-auto flex items-center justify-center mb-3">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800">Attention queue is clear</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            All patients in Ward 3B are within expected bounds or being actively observed. No immediate bedside actions needed for this 15-minute window.
          </p>
        </div>
      )}

      {/* Task Cards Grid (Side by Side) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {visibleTasks.map((task, index) => {
          const rankNumber = index + 1;
          const wardBed = wardBeds.find((b) => b.bed === task.bed);
          const detail = patientDetailsMap[task.bed];
          const isEscalation = task.escalated || task.type === 'page_doctor';
          const vitals = parseVitalsFromTask(task, detail);
          const actionSteps = getActionSteps(task);
          const patientLabel = getPatientLabel(task.bed, wardBed, detail);

          // Card accent styling
          const accentBorderColor = isEscalation
            ? 'border-l-4 border-l-amber-500'
            : 'border-l-4 border-l-purple-500';

          return (
            <article
              key={task.id}
              className={`bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between ${accentBorderColor}`}
            >
              <div>
                {/* Top Row: Bed number, Rank, and Action Badge */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-black text-slate-900 leading-none">
                      BED {task.bed}
                    </span>
                    <span className="text-xs font-bold text-slate-400">
                      #{rankNumber}
                    </span>
                  </div>

                  {/* Action Badge */}
                  {isEscalation ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200/80 shadow-2xs">
                      <PhoneCall className="w-3.5 h-3.5" />
                      <span>ESCALATE</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-purple-50 text-purple-700 border border-purple-200/80 shadow-2xs">
                      <Stethoscope className="w-3.5 h-3.5" />
                      <span>BEDSIDE ACTION</span>
                    </span>
                  )}
                </div>

                {/* Patient Anonymous Descriptor */}
                <div
                  onClick={() => onSelectBed(task.bed)}
                  className="mt-1.5 text-xs text-slate-500 font-medium hover:text-teal-700 cursor-pointer flex items-center gap-1.5 transition"
                  title="Click to view full patient vitals chart"
                >
                  <span>{patientLabel}</span>
                  <span className="text-slate-300">•</span>
                  <span className="text-[11px] text-teal-600 font-bold hover:underline">
                    View Chart →
                  </span>
                </div>

                {/* Headline Sentence (Built from task.reason, prioritizing clinical pattern line) */}
                <h3 className="mt-3 text-base font-extrabold text-slate-900 leading-snug">
                  {formatCardReason(task.reason, task.title, detail?.assessment?.reasons)}
                </h3>

                {/* Key Vitals Display with Baseline Comparisons & Arrows */}
                {vitals.length > 0 && (
                  <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 py-1">
                    {vitals.map((v, i) => (
                      <div key={i} className="flex items-center gap-1 text-xs">
                        <span className="font-bold text-slate-500 uppercase">{v.name}</span>
                        <span className="font-black text-amber-700 text-sm">{v.value}</span>
                        {v.baseline && (
                          <span className="text-[11px] text-slate-400 font-medium">
                            (base {v.baseline})
                          </span>
                        )}
                        {v.trend === 'up' && (
                          <ArrowUp className="w-3.5 h-3.5 text-amber-600 stroke-[2.5]" />
                        )}
                        {v.trend === 'down' && (
                          <ArrowDown className="w-3.5 h-3.5 text-blue-600 stroke-[2.5]" />
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* DATA AGE Chips Row */}
                <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[11px]">
                  <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                    DATA AGE
                  </span>

                  {/* Vitals Age Chips */}
                  {getVitalsAgeChips(detail, simTime, wardBed).map((chip) => {
                    const dotColor =
                      chip.status === 'stale'
                        ? 'bg-rose-500'
                        : chip.status === 'due'
                        ? 'bg-amber-500'
                        : 'bg-emerald-500';
                    return (
                      <div
                        key={chip.name}
                        className="inline-flex items-center gap-1 text-slate-600 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-100 font-medium"
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
                        <span>{chip.name} {chip.age}</span>
                      </div>
                    );
                  })}
                </div>

                {/* DO NOW Numbered List of Closed-Set Card Actions */}
                <div className="mt-4 bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/60">
                  <div className="text-[10px] font-black uppercase tracking-wider text-purple-900/80 mb-2.5 flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-purple-600" />
                    <span>DO NOW</span>
                  </div>

                  <ol className="space-y-2">
                    {actionSteps.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-800 font-semibold">
                        <span className="w-4 h-4 rounded-full bg-purple-600 text-white text-[10px] font-black flex items-center justify-center shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <div className="flex-1 flex items-baseline justify-between gap-2">
                          <span className="leading-snug">{step.text}</span>
                          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-tight shrink-0">
                            {step.code}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>

              {/* Action Buttons at Bottom */}
              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                {/* Left Primary/Secondary Actions */}
                <div className="flex items-center gap-2 flex-1">
                  {isEscalation ? (
                    <>
                      <button
                        onClick={() => alert(`Paged on-duty Medical Officer for Bed ${task.bed} (SBAR clinical handoff packet dispatched).`)}
                        className="flex-1 bg-amber-600 hover:bg-amber-700 text-white px-3.5 py-2 rounded-xl text-xs font-bold shadow-xs flex items-center justify-center gap-1.5 transition active:scale-98"
                      >
                        <PhoneCall className="w-3.5 h-3.5" />
                        <span>Page doctor</span>
                      </button>
                      <button
                        onClick={() => handleDone(task.id)}
                        disabled={completingTaskId === task.id}
                        className={`px-3.5 py-2 rounded-xl border text-xs font-bold transition flex items-center gap-1.5 ${
                          completingTaskId === task.id
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                            : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <CheckCircle2 className={`w-3.5 h-3.5 ${completingTaskId === task.id ? 'text-emerald-700' : 'text-emerald-600'}`} />
                        <span>{completingTaskId === task.id ? 'Done ✓' : 'Done'}</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => handleDone(task.id)}
                        disabled={completingTaskId === task.id}
                        className={`flex-1 px-3.5 py-2 rounded-xl text-xs font-bold shadow-xs flex items-center justify-center gap-1.5 transition active:scale-98 ${
                          completingTaskId === task.id
                            ? 'bg-emerald-600 text-white'
                            : 'bg-purple-700 hover:bg-purple-800 text-white'
                        }`}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{completingTaskId === task.id ? 'Done ✓' : 'Done'}</span>
                      </button>
                      <button
                        onClick={() => alert(`Paged on-duty Medical Officer for Bed ${task.bed}.`)}
                        className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold transition flex items-center gap-1.5"
                      >
                        <PhoneCall className="w-3.5 h-3.5 text-slate-500" />
                        <span>Page doctor</span>
                      </button>
                    </>
                  )}
                </div>

                {/* Snooze Button (Local UI State Only) */}
                <div className="relative">
                  <button
                    onClick={() =>
                      setSnoozeMenuOpen(snoozeMenuOpen === task.id ? null : task.id)
                    }
                    className="flex items-center gap-1 text-slate-500 hover:text-slate-800 px-2.5 py-2 rounded-xl hover:bg-slate-100 text-xs font-semibold transition"
                    title="Snooze this card for this attention window"
                  >
                    <BellOff className="w-3.5 h-3.5" />
                    <span>Snooze</span>
                    <ChevronDown className="w-3 h-3" />
                  </button>

                  {snoozeMenuOpen === task.id && (
                    <div className="absolute right-0 bottom-full mb-1 w-36 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-30 text-xs">
                      <button
                        onClick={() => {
                          onSnoozeTask(task.id);
                          setSnoozeMenuOpen(null);
                        }}
                        className="w-full text-left px-3 py-1.5 text-slate-700 hover:bg-slate-50 font-medium"
                      >
                        Snooze 15 min
                      </button>
                      <button
                        onClick={() => {
                          onAction(task.id, 'not-useful');
                          setSnoozeMenuOpen(null);
                        }}
                        className="w-full text-left px-3 py-1.5 text-rose-600 hover:bg-rose-50 font-medium"
                      >
                        Dismiss (Not useful)
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
};
