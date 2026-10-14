import React from 'react';
import { WardBed, WardStatus, Task, PatientDetail } from '../types';
import { Clock, AlertCircle, Sparkles, CheckCircle2, AlertOctagon } from 'lucide-react';
import { extractPatternReason } from '../utils/reasons';

interface WardStripProps {
  beds: WardBed[];
  selectedBedId: number | null;
  onSelectBed: (bed: number) => void;
  tasks?: Task[];
  patientDetailsMap?: Record<number, PatientDetail>;
}

export const WardStrip: React.FC<WardStripProps> = ({
  beds,
  selectedBedId,
  onSelectBed,
  tasks = [],
  patientDetailsMap = {},
}) => {
  const getStatusStyles = (status: WardStatus) => {
    switch (status) {
      case 'critical':
        return {
          bg: 'bg-rose-50 border-rose-300 hover:border-rose-500 text-rose-900',
          badge: 'bg-rose-600 text-white',
          label: 'CRITICAL',
          icon: <AlertOctagon className="w-3 h-3 text-rose-600" />,
        };
      case 'action':
        return {
          bg: 'bg-amber-50 border-amber-300 hover:border-amber-500 text-amber-900',
          badge: 'bg-amber-600 text-white',
          label: 'ACTION',
          icon: <AlertCircle className="w-3 h-3 text-amber-600" />,
        };
      case 'watch':
        return {
          bg: 'bg-yellow-50/70 border-yellow-200 hover:border-yellow-400 text-yellow-900',
          badge: 'bg-yellow-500 text-white',
          label: 'WATCH',
          icon: <Clock className="w-3 h-3 text-yellow-600" />,
        };
      case 'stable':
      default:
        return {
          bg: 'bg-white border-slate-200 hover:border-slate-400 text-slate-800',
          badge: 'bg-emerald-600 text-white',
          label: 'STABLE',
          icon: <CheckCircle2 className="w-3 h-3 text-emerald-600" />,
        };
    }
  };

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-900 m-0">20-Bed Ward Overview</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Click any bed to inspect personal baselines, vitals sparklines, and active clinical risk
          </p>
        </div>

        {/* Legend for color-blind accessibility */}
        <div className="flex items-center gap-3 text-xs font-medium text-slate-600">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>Stable</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
            <span>Watch</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span>Action</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-600" />
            <span>Critical</span>
          </div>
        </div>
      </div>

      {/* 20 Bed Tiles Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-10 gap-2.5">
        {beds.map((b) => {
          const style = getStatusStyles(b.status);
          const isSelected = selectedBedId === b.bed;
          const matchingTask = tasks.find((t) => t.bed === b.bed);
          const matchingDetail = patientDetailsMap[b.bed];
          const patternLine =
            extractPatternReason(matchingTask?.reason) ||
            extractPatternReason(matchingDetail?.assessment?.reasons);

          return (
            <button
              key={b.bed}
              onClick={() => onSelectBed(b.bed)}
              className={`p-2 rounded-xl border transition-all text-left relative flex flex-col justify-between min-h-[96px] ${
                style.bg
              } ${
                isSelected
                  ? 'ring-2 ring-teal-500 shadow-md scale-[1.02] border-teal-500'
                  : 'hover:shadow-sm'
              }`}
              title={patternLine ? `Bed ${b.bed}: ${patternLine}` : `Bed ${b.bed}: ${b.status}`}
            >
              {/* Top row: Bed number & Status badge */}
              <div className="flex items-center justify-between w-full">
                <span className="text-xs font-black tracking-tight text-slate-900">
                  BED {b.bed}
                </span>
                {style.icon}
              </div>

              {/* Conditions chips & Pattern line */}
              <div className="my-1 space-y-1">
                <div className="flex flex-wrap gap-0.5">
                  {b.conditions.map((c) => (
                    <span
                      key={c}
                      className="text-[9px] font-semibold px-1 py-0.2 rounded bg-slate-200/80 text-slate-700 uppercase"
                    >
                      {c === 'post_op' ? 'Post-Op' : c.toUpperCase()}
                    </span>
                  ))}
                </div>

                {patternLine && (
                  <span className="text-[9px] font-bold text-teal-900 bg-teal-100/90 border border-teal-200 px-1 py-0.5 rounded block truncate leading-tight">
                    {patternLine}
                  </span>
                )}
              </div>

              {/* Bottom row: Stale marker or Task marker */}
              <div className="flex items-center justify-between text-[10px] font-mono mt-auto pt-1 border-t border-slate-200/50">
                {b.data_stale ? (
                  <span className="text-amber-800 font-bold bg-amber-200/60 px-1 rounded flex items-center gap-0.5">
                    <Clock className="w-2.5 h-2.5" /> STALE
                  </span>
                ) : (
                  <span className="text-slate-500">
                    {b.hours_since_last_vitals !== null ? `${b.hours_since_last_vitals?.toFixed(1)}h` : '-'}
                  </span>
                )}

                {b.has_open_task && (
                  <span className="w-2 h-2 rounded-full bg-teal-600 animate-ping" title="Open task pending" />
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
