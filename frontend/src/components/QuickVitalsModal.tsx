import React, { useState, useEffect } from 'react';
import { Consciousness, VitalsIn } from '../types';
import { X, Check, AlertCircle, Heart, Thermometer, Wind, Activity } from 'lucide-react';

interface QuickVitalsModalProps {
  initialBed?: number | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (vitals: VitalsIn) => Promise<void>;
}

export const QuickVitalsModal: React.FC<QuickVitalsModalProps> = ({
  initialBed,
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [bed, setBed] = useState<number>(initialBed || 1);
  const [hr, setHr] = useState<string>('');
  const [sbp, setSbp] = useState<string>('');
  const [dbp, setDbp] = useState<string>('');
  const [rr, setRr] = useState<string>('');
  const [spo2, setSpo2] = useState<string>('');
  const [temp, setTemp] = useState<string>('');
  const [onOxygen, setOnOxygen] = useState<boolean>(false);
  const [consciousness, setConsciousness] = useState<Consciousness>('A');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (initialBed) setBed(initialBed);
  }, [initialBed]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const hrVal = hr ? parseFloat(hr) : null;
    const sbpVal = sbp ? parseFloat(sbp) : null;
    const dbpVal = dbp ? parseFloat(dbp) : null;
    const rrVal = rr ? parseFloat(rr) : null;
    const spo2Val = spo2 ? parseFloat(spo2) : null;
    const tempVal = temp ? parseFloat(temp) : null;

    // Validation: at least one vital
    if (
      hrVal === null &&
      sbpVal === null &&
      dbpVal === null &&
      rrVal === null &&
      spo2Val === null &&
      tempVal === null
    ) {
      setError('Please provide at least one vital sign measurement.');
      return;
    }

    // Validation: SBP >= DBP
    if (sbpVal !== null && dbpVal !== null && sbpVal < dbpVal) {
      setError('Systolic BP (SBP) must be greater than or equal to Diastolic BP (DBP).');
      return;
    }

    // Bounds validation
    if (hrVal !== null && (hrVal < 0 || hrVal > 300)) {
      setError('Heart Rate must be between 0 and 300 bpm.');
      return;
    }
    if (rrVal !== null && (rrVal < 0 || rrVal > 80)) {
      setError('Breathing Rate must be between 0 and 80 /min.');
      return;
    }
    if (spo2Val !== null && (spo2Val < 0 || spo2Val > 100)) {
      setError('SpO2 must be between 0 and 100%.');
      return;
    }
    if (tempVal !== null && (tempVal < 25 || tempVal > 45)) {
      setError('Temperature must be between 25.0 and 45.0 °C.');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        patient_id: bed, // patient_id corresponds to bed in standard setup
        hr: hrVal,
        sbp: sbpVal,
        dbp: dbpVal,
        rr: rrVal,
        spo2: spo2Val,
        temp: tempVal,
        on_oxygen: onOxygen,
        consciousness: consciousness,
        source: 'manual',
      });
      // Reset form
      setHr('');
      setSbp('');
      setDbp('');
      setRr('');
      setSpo2('');
      setTemp('');
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to submit vitals.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-lg w-full overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-teal-500 text-slate-950 rounded-xl">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white m-0">Quick Vitals Entry</h2>
              <p className="text-xs text-slate-400">Fast tablet entry • Automatic re-evaluation</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Bed Selector */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
              Select Bed Number
            </label>
            <select
              value={bed}
              onChange={(e) => setBed(parseInt(e.target.value, 10))}
              className="w-full rounded-xl border border-slate-300 p-2.5 text-sm font-bold text-slate-900 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-500 outline-none transition"
            >
              {Array.from({ length: 20 }, (_, i) => i + 1).map((b) => (
                <option key={b} value={b}>
                  Bed {b} {b === 7 ? '(Post-Op)' : b === 3 ? '(COPD)' : b === 12 ? '(Cardiac / Crash)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Vitals Inputs Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Heart Rate (bpm)
              </label>
              <input
                type="number"
                placeholder="e.g. 78"
                value={hr}
                onChange={(e) => setHr(e.target.value)}
                className="w-full rounded-xl border border-slate-300 p-2.5 text-sm font-mono focus:ring-2 focus:ring-teal-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Breathing Rate (RR /min)
              </label>
              <input
                type="number"
                placeholder="e.g. 18"
                value={rr}
                onChange={(e) => setRr(e.target.value)}
                className="w-full rounded-xl border border-slate-300 p-2.5 text-sm font-mono focus:ring-2 focus:ring-teal-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Systolic BP (SBP mmHg)
              </label>
              <input
                type="number"
                placeholder="e.g. 120"
                value={sbp}
                onChange={(e) => setSbp(e.target.value)}
                className="w-full rounded-xl border border-slate-300 p-2.5 text-sm font-mono focus:ring-2 focus:ring-teal-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Diastolic BP (DBP mmHg)
              </label>
              <input
                type="number"
                placeholder="e.g. 80"
                value={dbp}
                onChange={(e) => setDbp(e.target.value)}
                className="w-full rounded-xl border border-slate-300 p-2.5 text-sm font-mono focus:ring-2 focus:ring-teal-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Oxygen Sat. (SpO2 %)
              </label>
              <input
                type="number"
                placeholder="e.g. 98"
                value={spo2}
                onChange={(e) => setSpo2(e.target.value)}
                className="w-full rounded-xl border border-slate-300 p-2.5 text-sm font-mono focus:ring-2 focus:ring-teal-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Temperature (°C)
              </label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g. 36.8"
                value={temp}
                onChange={(e) => setTemp(e.target.value)}
                className="w-full rounded-xl border border-slate-300 p-2.5 text-sm font-mono focus:ring-2 focus:ring-teal-500 outline-none"
              />
            </div>
          </div>

          {/* Oxygen & ACVPU scale */}
          <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-t border-slate-100">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={onOxygen}
                onChange={(e) => setOnOxygen(e.target.checked)}
                className="w-4 h-4 rounded text-teal-600 focus:ring-teal-500"
              />
              <span>Supplemental Oxygen</span>
            </label>

            <div className="flex items-center gap-1.5 text-xs text-slate-600">
              <span className="font-semibold">Consciousness:</span>
              {(['A', 'C', 'V', 'P', 'U'] as Consciousness[]).map((c) => (
                <button
                  type="button"
                  key={c}
                  onClick={() => setConsciousness(c)}
                  className={`px-2 py-1 rounded-lg text-xs font-bold transition ${
                    consciousness === c
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Action Button */}
          <div className="pt-3">
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 rounded-2xl font-bold text-sm bg-teal-600 hover:bg-teal-700 text-white shadow-md flex items-center justify-center gap-2 transition active:scale-98 disabled:opacity-50"
            >
              <Check className="w-5 h-5" />
              <span>{submitting ? 'Submitting...' : 'Record Vitals & Re-evaluate'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
