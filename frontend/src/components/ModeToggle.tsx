import React from 'react';
import { Mode } from '../types';
import { AlertTriangle, Sparkles, Filter, BellRing } from 'lucide-react';

interface ModeToggleProps {
  mode: Mode;
  alertsShown: number;
  onModeChange: (newMode: Mode) => void;
}

export const ModeToggle: React.FC<ModeToggleProps> = ({ mode, alertsShown, onModeChange }) => {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200/80 flex flex-col md:flex-row items-center justify-between gap-4">
      {/* Selector Tabs */}
      <div className="flex items-center bg-slate-100 p-1.5 rounded-xl border border-slate-200 w-full md:w-auto">
        <button
          onClick={() => onModeChange('wardpulse')}
          className={`flex-1 md:flex-initial px-5 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
            mode === 'wardpulse'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
          }`}
        >
          <Sparkles className="w-4 h-4 text-teal-200" />
          <span>WardPulse (AI Early Warning)</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-teal-800 text-teal-100 font-normal">
            Max 2 actions
          </span>
        </button>

        <button
          onClick={() => onModeChange('news2')}
          className={`flex-1 md:flex-initial px-5 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
            mode === 'news2'
              ? 'bg-rose-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
          }`}
        >
          <BellRing className="w-4 h-4 text-rose-200" />
          <span>Naive AI (Standard NEWS2)</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-rose-800 text-rose-100 font-normal">
            Threshold
          </span>
        </button>
      </div>

      {/* Prominent Alert Counter */}
      <div className="flex items-center gap-4 w-full md:w-auto justify-end">
        <div
          className={`flex items-center gap-3 px-4 py-2 rounded-xl border transition-all ${
            mode === 'wardpulse'
              ? 'bg-teal-50 border-teal-200 text-teal-900'
              : 'bg-rose-50 border-rose-200 text-rose-900'
          }`}
        >
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg shadow-sm ${
              mode === 'wardpulse' ? 'bg-teal-600 text-white' : 'bg-rose-600 text-white'
            }`}
          >
            {alertsShown}
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Demands on Nurse
            </div>
            <div className="text-sm font-bold flex items-center gap-1.5">
              {mode === 'wardpulse' ? (
                <>
                  <span>Top actions prioritised</span>
                  <span className="text-xs font-medium px-2 py-0.5 bg-teal-200/70 text-teal-800 rounded-full">
                    -73% noise
                  </span>
                </>
              ) : (
                <>
                  <span className="text-rose-700">Alert Fatigue Warning</span>
                  <AlertTriangle className="w-4 h-4 text-rose-500" />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Short insight indicator */}
        <div className="hidden lg:block text-xs text-slate-500 max-w-xs leading-snug">
          {mode === 'wardpulse' ? (
            <span>
              <strong>Personal baseline filter:</strong> Stable chronic COPD (Bed 3) is quiet; deteriorating post-op (Bed 7) is escalated.
            </span>
          ) : (
            <span>
              <strong>Fixed threshold flaw:</strong> Every abnormal vital rings alarms indiscriminately regardless of baseline or urgency.
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
