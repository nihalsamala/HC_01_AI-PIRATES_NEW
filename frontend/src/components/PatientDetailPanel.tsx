import React from 'react';
import { PatientDetail, RiskTier } from '../types';
import { X, User, HeartPulse, Clock, AlertTriangle, PlusCircle, CheckCircle2 } from 'lucide-react';
import { Sparkline } from './Sparkline';

interface PatientDetailPanelProps {
  detail: PatientDetail | null;
  onClose: () => void;
  onOpenQuickVitals: (bed: number) => void;
}

export const PatientDetailPanel: React.FC<PatientDetailPanelProps> = ({
  detail,
  onClose,
  onOpenQuickVitals,
}) => {
  if (!detail) return null;

  const { patient, recent_vitals, assessment, open_tasks } = detail;

  const getTierBadge = (tier?: RiskTier) => {
    switch (tier) {
      case 'critical':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'high':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  const hrSeries = recent_vitals.map((v) => v.hr).filter((v): v is number => v !== null && v !== undefined);
  const sbpSeries = recent_vitals.map((v) => v.sbp).filter((v): v is number => v !== null && v !== undefined);
  const rrSeries = recent_vitals.map((v) => v.rr).filter((v): v is number => v !== null && v !== undefined);
  const spo2Series = recent_vitals.map((v) => v.spo2).filter((v): v is number => v !== null && v !== undefined);
  const tempSeries = recent_vitals.map((v) => v.temp).filter((v): v is number => v !== null && v !== undefined);

  const latestReading = recent_vitals[recent_vitals.length - 1];

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-white shadow-2xl border-l border-slate-200 z-50 flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="p-5 border-b border-slate-200 bg-slate-900 text-white flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-teal-500 text-slate-950 flex items-center justify-center font-bold">
            {patient.bed}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white m-0">
                Bed {patient.bed} — {patient.display_name || `Patient ${patient.id}`}
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              Age {patient.age} • Admitted {new Date(patient.admitted_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Condition Tags */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
            Clinical Baseline Conditions
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {patient.conditions.length > 0 ? (
              patient.conditions.map((c) => (
                <span
                  key={c}
                  className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-teal-50 text-teal-800 border border-teal-200"
                >
                  {c === 'copd' && 'COPD (Elevated baseline RR expected)'}
                  {c === 'post_op' && 'Post-Op (Monitored for infection/hypovolemia)'}
                  {c === 'cardiac' && 'Cardiac History (BP/HR fluctuation)'}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500 italic">No specific baseline flags</span>
            )}
          </div>
        </div>

        {/* Risk Assessment Box */}
        {assessment && (
          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                WardPulse Risk Assessment
              </span>
              <span
                className={`text-xs font-bold px-2.5 py-0.5 rounded-full border uppercase ${getTierBadge(
                  assessment.risk_tier
                )}`}
              >
                {assessment.risk_tier} Risk ({Math.round(assessment.risk_score * 100)}%)
              </span>
            </div>

            {/* Reasons list */}
            <div className="space-y-1">
              {assessment.reasons.map((r, i) => (
                <div key={i} className="flex items-start gap-1.5 text-xs text-slate-700">
                  <span className="text-teal-600 font-bold">•</span>
                  <span>{r}</span>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-500 font-mono">
              <span>NEWS2 Score: {assessment.news2_score ?? 'N/A'}</span>
              <span>
                Last vitals:{' '}
                {assessment.hours_since_last_vitals !== null
                  ? `${assessment.hours_since_last_vitals?.toFixed(1)}h ago`
                  : 'N/A'}
              </span>
            </div>
          </div>
        )}

        {/* Sparkline Vital Trends */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 m-0">
              Vital Sign Trends (Recent 24h)
            </h3>
            <span className="text-[10px] text-slate-400">Inline Sparklines</span>
          </div>

          <div className="space-y-1">
            <Sparkline
              label="Heart Rate"
              data={hrSeries}
              unit="bpm"
              color="#0284c7"
              currentValue={latestReading?.hr}
            />
            <Sparkline
              label="Blood Press."
              data={sbpSeries}
              unit="mmHg"
              color="#0d9488"
              currentValue={latestReading?.sbp ? `${latestReading.sbp}/${latestReading.dbp ?? '-'}` : null}
            />
            <Sparkline
              label="Breathing (RR)"
              data={rrSeries}
              unit="/min"
              color="#7c3aed"
              currentValue={latestReading?.rr}
            />
            <Sparkline
              label="SpO2 Sat."
              data={spo2Series}
              unit="%"
              color="#e11d48"
              currentValue={latestReading?.spo2}
            />
            <Sparkline
              label="Temp"
              data={tempSeries}
              unit="°C"
              color="#d97706"
              currentValue={latestReading?.temp}
            />
          </div>
        </div>

        {/* Open Tasks for this bed */}
        {open_tasks && open_tasks.length > 0 && (
          <div className="bg-amber-50 rounded-2xl p-4 border border-amber-200 space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-900 m-0">
              Pending Actions for Bed {patient.bed}
            </h3>
            {open_tasks.map((t) => (
              <div key={t.id} className="text-xs text-amber-950 font-medium">
                • {t.title} — <span className="text-amber-800">{t.reason}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer CTA */}
      <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
        <button
          onClick={() => {
            onClose();
            onOpenQuickVitals(patient.bed);
          }}
          className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-teal-600 hover:bg-teal-700 text-white shadow-sm flex items-center justify-center gap-1.5 transition active:scale-95"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Enter Vitals for Bed {patient.bed}</span>
        </button>
      </div>
    </div>
  );
};
