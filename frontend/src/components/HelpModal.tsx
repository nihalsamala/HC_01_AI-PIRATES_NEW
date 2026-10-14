import React from 'react';
import { X, ShieldCheck, HeartPulse, Sparkles, Filter, AlertTriangle } from 'lucide-react';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-teal-500 text-slate-950 rounded-xl">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white m-0">How WardPulse Works</h2>
              <p className="text-xs text-slate-400">Clinical decision support rationale & demo guide</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs text-slate-600 leading-relaxed">
          <div className="bg-teal-50 p-4 rounded-2xl border border-teal-200 text-teal-900">
            <h3 className="text-sm font-bold mb-1 flex items-center gap-1.5 text-teal-950">
              <Sparkles className="w-4 h-4 text-teal-600" />
              The Core Problem: Alert Fatigue
            </h3>
            <p>
              Under standard hospital scoring (NEWS2), fixed thresholds trigger alarms on almost every abnormal reading regardless of a patient's individual baseline. In an understaffed 20-bed ward, this produces 10+ alerts simultaneously, causing nurses to miss genuine deterioration.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-1.5">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wide block">
                Story 1: The Personal Baseline
              </span>
              <p>
                <strong>Bed 3 (COPD)</strong> breathes at RR 22 every day. Naive NEWS2 triggers a red alarm every hour. WardPulse recognizes this as their personal baseline and stays quiet.
              </p>
              <p>
                <strong>Bed 7 (Post-op)</strong> usually breathes at RR 14. When their RR climbs to 22, WardPulse detects a +57% baseline breach and pages the doctor immediately.
              </p>
            </div>

            <div className="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-1.5">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wide block">
                Story 2: Freshness vs Alarm
              </span>
              <p>
                <strong>Bed 4</strong> has a stale BP reading (7.2 hours old). Naive systems panic or remain silent. WardPulse generates a specific <em>Repeat manual BP</em> card rather than paging a doctor on stale numbers.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-2xl border border-rose-200 bg-rose-50 text-rose-950 space-y-1">
            <span className="text-xs font-bold text-rose-900 uppercase tracking-wide flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
              Story 3: Unequivocal Crash Bypass
            </span>
            <p>
              <strong>Bed 12</strong> suffers severe hypotension and shock (SBP 78, HR 135, SpO2 86%). Regardless of the 2-action budget, safety rules bypass queuing and place an emergency card at the very top of the nurse's screen.
            </p>
          </div>

          <div className="p-3 bg-slate-100 rounded-xl text-slate-500 text-[11px]">
            <strong>Clinical Safety Guarantee:</strong> WardPulse is a decision support system, not a diagnostic device. All emergency crash red-lines bypass budget constraints to protect patient safety.
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-xs font-bold bg-slate-900 text-white hover:bg-slate-800 transition"
          >
            Got it, return to ward
          </button>
        </div>
      </div>
    </div>
  );
};
