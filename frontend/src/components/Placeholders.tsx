import React from 'react';
import {
  Map,
  ClipboardList,
  BookOpen,
  BarChart3,
  Brain,
  ArrowLeft,
  ShieldAlert,
  FileText,
  Activity,
  Layers,
} from 'lucide-react';
import { ActiveTab } from './NavSidebar';
import { EvalResults } from '../types';

interface PlaceholderViewProps {
  tab: ActiveTab;
  onBackToConsole: () => void;
  evalResults: EvalResults | null;
}

export const PlaceholderView: React.FC<PlaceholderViewProps> = ({
  tab,
  onBackToConsole,
  evalResults,
}) => {
  if (tab === 'ward_map') {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center">
              <Map className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-900">Ward 3B Floor Plan &amp; Spatial Map</h1>
              <p className="text-xs text-slate-500 font-medium">
                Physical layout of 20 beds with distance to nursing station
              </p>
            </div>
          </div>
          <button
            onClick={onBackToConsole}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Console</span>
          </button>
        </div>

        {/* Visual Bed Layout Map */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 bg-slate-50 rounded-2xl border border-slate-200">
          {Array.from({ length: 20 }, (_, i) => i + 1).map((b) => (
            <div
              key={b}
              className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex flex-col justify-between h-24 hover:border-teal-500 cursor-pointer transition"
            >
              <div className="flex justify-between items-center">
                <span className="font-extrabold text-sm text-slate-800">Bed {b}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
              </div>
              <span className="text-[11px] text-slate-500">Bay {Math.ceil(b / 5)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (tab === 'handover') {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center">
              <ClipboardList className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-900">Shift Handover (SBAR Summary)</h1>
              <p className="text-xs text-slate-500 font-medium">
                Automated clinical synthesis for incoming nursing team
              </p>
            </div>
          </div>
          <button
            onClick={onBackToConsole}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Console</span>
          </button>
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200 text-amber-950">
            <h3 className="text-xs font-black uppercase tracking-wider text-amber-800 mb-1">
              Situation &amp; Key Watch Patients
            </h3>
            <p className="text-sm font-semibold">
              Bed 7 (Post-op, 28M): Temperature 37.7°C, pulse 108. Escalated doctor review requested.
            </p>
            <p className="text-sm font-semibold mt-1">
              Bed 9 (COPD, 70M): Cannula adjustment completed, SpO2 92% on 2L O2.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (tab === 'protocols') {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-900">Ward Deterioration Protocols</h1>
              <p className="text-xs text-slate-500 font-medium">
                Standardised bedside action codes &amp; escalation tiers
              </p>
            </div>
          </div>
          <button
            onClick={onBackToConsole}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Console</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { code: 'A01', title: 'Sit patient upright to 45°', desc: 'Increases thoracic lung volume and improves diaphragmatic excursion.' },
            { code: 'A02', title: 'Check oxygen delivery & cannula', desc: 'Verify cannula placement, tubing kinks, and flow meter setting.' },
            { code: 'A05', title: 'Check temperature & rigors', desc: 'Assess for septic spike, diaphoresis, or chills.' },
            { code: 'A08', title: 'Full vitals recheck', desc: 'Acquire complete 6-vital set to recalibrate personal trajectory.' },
            { code: 'A09', title: 'Page on-duty doctor', desc: 'Activate structured SBAR handoff for rapid medical officer assessment.' },
          ].map((item) => (
            <div key={item.code} className="p-4 rounded-xl border border-slate-200 bg-slate-50/70">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-black bg-purple-100 text-purple-800 px-2 py-0.5 rounded-md">
                  {item.code}
                </span>
                <span className="text-sm font-bold text-slate-800">{item.title}</span>
              </div>
              <p className="text-xs text-slate-600 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (tab === 'proof') {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-900">Live Proof &amp; Evaluation Benchmark</h1>
              <p className="text-xs text-slate-500 font-medium">
                Rigorous side-by-side comparison vs traditional threshold systems
              </p>
            </div>
          </div>
          <button
            onClick={onBackToConsole}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Console</span>
          </button>
        </div>

        {evalResults && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {evalResults.systems.map((s) => (
              <div
                key={s.system}
                className={`p-5 rounded-2xl border ${
                  s.system === 'wardpulse'
                    ? 'border-teal-300 bg-teal-50/50'
                    : 'border-slate-200 bg-slate-50'
                }`}
              >
                <h3 className="text-base font-extrabold uppercase tracking-wide text-slate-900">
                  {s.system === 'wardpulse' ? 'WardPulse Engine' : 'Naïve NEWS2 Baseline'}
                </h3>
                <div className="mt-4 space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-500">Alerts / nurse-hour:</span>
                    <span className="font-bold font-mono text-slate-800">{s.alerts_per_nurse_hour ?? 'N/A'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-500">Sensitivity:</span>
                    <span className="font-bold font-mono text-slate-800">
                      {s.sensitivity ? `${(s.sensitivity * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Median lead time:</span>
                    <span className="font-bold font-mono text-slate-800">{s.median_lead_time_hours ?? 'N/A'} hrs</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // how_it_thinks
  return (
    <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xs space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-black text-slate-900">How WardPulse Thinks</h1>
            <p className="text-xs text-slate-500 font-medium">
              Dual-horizon personal baselines, bounded attention budget &amp; closed-set safety
            </p>
          </div>
        </div>
        <button
          onClick={onBackToConsole}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Console</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
          <h3 className="font-bold text-sm text-slate-800">1. Personal Baseline</h3>
          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            Replaces rigid universal thresholds with patient-specific baselines blended from admission priors and recent 24-hour vitals.
          </p>
        </div>
        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
          <h3 className="font-bold text-sm text-slate-800">2. Attention Allocator</h3>
          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            Respects the nurse's cognitive bandwidth by bounding output to at most K cards (default 2) for the next 15 minutes.
          </p>
        </div>
        <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
          <h3 className="font-bold text-sm text-slate-800">3. Closed Action Set</h3>
          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            Eliminates LLM hallucination and dangerous freeform drug recommendations by selecting exclusively from pre-authorized protocols.
          </p>
        </div>
      </div>
    </div>
  );
};
