import React, { useState } from 'react';
import { AlertTriangle, X, Send, HeartHandshake } from 'lucide-react';

interface WorriedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (bed: number, concernNote: string) => void;
  currentSelectedBed?: number | null;
}

export const WorriedModal: React.FC<WorriedModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  currentSelectedBed,
}) => {
  const [bed, setBed] = useState<number>(currentSelectedBed || 7);
  const [selectedPreset, setSelectedPreset] = useState<string>('Nurse gut instinct / looks unwell');
  const [customNote, setCustomNote] = useState<string>('');

  if (!isOpen) return null;

  const presets = [
    'Nurse gut instinct / looks unwell',
    'Breathing pattern or work of breathing changed',
    'Color pale, mottled, or cold periphery',
    'Agitated, confused, or unusually drowsy',
    'Family or patient expressed sudden dread',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const note = customNote ? `${selectedPreset}: ${customNote}` : selectedPreset;
    onSubmit(bed, note);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
      <div className="bg-white rounded-3xl max-w-md w-full border border-slate-200 shadow-2xl p-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-200">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-black text-slate-900 leading-tight">
                "I'm Worried" Bedside Escalation
              </h2>
              <p className="text-xs text-slate-500 font-medium">
                Clinical concern bypasses numerical thresholds
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Select Patient Bed
            </label>
            <select
              value={bed}
              onChange={(e) => setBed(parseInt(e.target.value, 10))}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm font-bold text-slate-800 focus:outline-teal-600"
            >
              {Array.from({ length: 20 }, (_, i) => i + 1).map((b) => (
                <option key={b} value={b}>
                  Bed {b}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Clinical Observation
            </label>
            <div className="space-y-1.5">
              {presets.map((preset) => (
                <label
                  key={preset}
                  className={`flex items-center gap-2.5 p-2 rounded-xl text-xs font-semibold cursor-pointer border transition ${
                    selectedPreset === preset
                      ? 'bg-rose-50 border-rose-300 text-rose-900'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="preset"
                    checked={selectedPreset === preset}
                    onChange={() => setSelectedPreset(preset)}
                    className="text-rose-600 focus:ring-rose-500"
                  />
                  <span>{preset}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Additional SBAR notes (optional)
            </label>
            <textarea
              value={customNote}
              onChange={(e) => setCustomNote(e.target.value)}
              placeholder="e.g. Patient looks dusky after mobilization, requesting doctor review..."
              rows={2}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-800 focus:outline-teal-600"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-bold text-xs hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-md flex items-center gap-2 transition active:scale-98"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Flag to Attention Engine</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
