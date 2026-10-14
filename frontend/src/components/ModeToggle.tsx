import React, { useState } from 'react';
import { Mode } from '../types';
import { AlertTriangle, Sparkles, Filter, BellRing, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

interface ModeToggleProps {
  mode: Mode;
  alertsShown: number;
  onModeChange: (newMode: Mode) => void;
}

export const ModeToggle: React.FC<ModeToggleProps> = ({ mode, alertsShown, onModeChange }) => {
  const [showGuide, setShowGuide] = useState<boolean>(false);

  return (
    <div className="space-y-2">
      <div className="bg-white rounded-3xl p-4 sm:p-5 shadow-sm border border-slate-200 flex flex-col md:flex-row items-center justify-between gap-4 transition-all">
        {/* Selector Tabs */}
        <div className="flex items-center bg-slate-100 p-1.5 rounded-2xl border border-slate-200/80 w-full md:w-auto shadow-inner">
          <button
            onClick={() => onModeChange('wardpulse')}
            className={`flex-1 md:flex-initial px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center justify-center gap-2 ${
              mode === 'wardpulse'
                ? 'bg-teal-600 text-white shadow-md'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            }`}
          >
            <Sparkles className="w-4 h-4 text-teal-200" />
            <span>WardPulse (AI Attention Allocator)</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-teal-800 text-teal-100 font-semibold">
              Max 2 actions
            </span>
          </button>

          <button
            onClick={() => onModeChange('news2')}
            className={`flex-1 md:flex-initial px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center justify-center gap-2 ${
              mode === 'news2'
                ? 'bg-rose-600 text-white shadow-md'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            }`}
          >
            <BellRing className="w-4 h-4 text-rose-200" />
            <span>Naive AI (Standard NEWS2)</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-rose-800 text-rose-100 font-semibold">
              Raw threshold
            </span>
          </button>
        </div>

        {/* Prominent Alert Counter & Visual Comparison */}
        <div className="flex items-center flex-wrap gap-4 w-full md:w-auto justify-end">
          <div
            className={`flex items-center gap-3 px-4 py-2.5 rounded-2xl border transition-all ${
              mode === 'wardpulse'
                ? 'bg-teal-50/80 border-teal-200 text-teal-950 shadow-sm'
                : 'bg-rose-50/80 border-rose-200 text-rose-950 shadow-sm'
            }`}
          >
            <div
              className={`badge-counter w-11 h-11 rounded-xl flex items-center justify-center font-black text-xl shadow-inner ${
                mode === 'wardpulse' ? 'bg-teal-600 text-white' : 'bg-rose-600 text-white'
              }`}
            >
              {alertsShown}
            </div>
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                Demands on Nurse Right Now
              </div>
              <div className="text-sm font-extrabold flex items-center gap-1.5">
                {mode === 'wardpulse' ? (
                  <>
                    <span>Top 2 Prioritised (15 min)</span>
                    <span className="text-xs font-semibold px-2 py-0.5 bg-teal-200 text-teal-900 rounded-full">
                      -73% noise
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-rose-700">Unbounded Alarm Flood</span>
                    <AlertTriangle className="w-4 h-4 text-rose-600 animate-pulse" />
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Quick Guide Toggle Button */}
          <button
            onClick={() => setShowGuide(!showGuide)}
            className="text-xs font-bold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-2 rounded-xl transition flex items-center gap-1.5 border border-slate-200"
            title="Toggle screen legend and visual guide"
          >
            <HelpCircle className="w-4 h-4 text-teal-600" />
            <span>How to read</span>
            {showGuide ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Collapsible 'How to read this screen' visual guide panel */}
      {showGuide && (
        <div className="bg-slate-900 text-white p-4 sm:p-5 rounded-3xl shadow-lg border border-slate-800 animate-in fade-in slide-in-from-top-2 duration-150 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-extrabold text-teal-300 uppercase tracking-wider flex items-center gap-1.5 m-0">
              <Sparkles className="w-3.5 h-3.5 text-teal-400" />
              How to Read the WardPulse Console (5-Second Guide)
            </h3>
            <button
              onClick={() => setShowGuide(false)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-slate-800/80 rounded-2xl border border-slate-700">
              <div className="flex items-center gap-2 mb-1">
                <span className="w-3 h-3 rounded-full bg-rose-500 shadow-sm" />
                <span className="font-bold text-white">RED: Action / Crash</span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                Acute deterioration or red-line breach. Unequivocal collapse appears in the top Emergency Banner.
              </p>
            </div>

            <div className="p-3 bg-slate-800/80 rounded-2xl border border-slate-700">
              <div className="flex items-center gap-2 mb-1">
                <span className="w-3 h-3 rounded-full bg-amber-400 shadow-sm" />
                <span className="font-bold text-white">YELLOW: Watch / Triage</span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                Borderline physiological trend or stale observations needing a routine repeat reading.
              </p>
            </div>

            <div className="p-3 bg-slate-800/80 rounded-2xl border border-slate-700">
              <div className="flex items-center gap-2 mb-1">
                <span className="w-3 h-3 rounded-full bg-emerald-400 shadow-sm" />
                <span className="font-bold text-white">GREEN: Baseline Stable</span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                Patient vitals align with established individual baselines (including chronic COPD).
              </p>
            </div>

            <div className="p-3 bg-slate-800/80 rounded-2xl border border-slate-700">
              <div className="flex items-center gap-2 mb-1">
                <span className="w-3 h-3 rounded-full border-2 border-dashed border-teal-400" />
                <span className="font-bold text-white">K = 2 Attention Budget</span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                At most 2 action cards are shown at once for the next 15 minutes to keep nursing staff focused and calm.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
