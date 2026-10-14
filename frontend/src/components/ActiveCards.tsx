import React from 'react';
import { Mode, Task } from '../types';
import { Check, X, AlertCircle, Clock, ChevronRight, UserCheck } from 'lucide-react';

interface ActiveCardsProps {
  tasks: Task[];
  mode: Mode;
  budgetK?: number | null;
  onAction: (taskId: number, action: 'done' | 'not-useful') => void;
  onSelectBed: (bed: number) => void;
}

export const ActiveCards: React.FC<ActiveCardsProps> = ({
  tasks,
  mode,
  budgetK,
  onAction,
  onSelectBed,
}) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-bold text-slate-800 m-0">
            {mode === 'wardpulse' ? 'Top Prioritised Actions' : 'Active Alarm Demands'}
          </h2>
          {mode === 'wardpulse' && budgetK && (
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-700 font-medium">
              Next 15 min focus (Budget: {budgetK})
            </span>
          )}
        </div>
        <span className="text-xs text-slate-500 font-mono">
          {tasks.length} {tasks.length === 1 ? 'action' : 'actions'} visible
        </span>
      </div>

      {tasks.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 border border-slate-200/80 text-center shadow-sm">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-3">
            <UserCheck className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-800">No active actions demanding attention</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            The ward is currently balanced. Scheduled observations and standby queues remain monitored.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tasks.map((task) => (
            <div
              key={task.id}
              className={`bg-white rounded-2xl p-5 border transition shadow-sm hover:shadow-md flex flex-col justify-between ${
                task.escalated
                  ? 'border-amber-400 bg-gradient-to-br from-amber-50/40 via-white to-white ring-1 ring-amber-400/50'
                  : 'border-slate-200/80 hover:border-slate-300'
              }`}
            >
              {/* Card Header: Bed, Title, Escalation */}
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onSelectBed(task.bed)}
                      className="text-xs font-black px-2.5 py-1 rounded-lg bg-slate-900 text-white hover:bg-slate-800 transition flex items-center gap-1 shadow-sm"
                    >
                      <span>BED {task.bed}</span>
                      <ChevronRight className="w-3 h-3 text-slate-400" />
                    </button>
                    <span className="text-xs font-mono text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Waited {Math.round(task.waiting_minutes)}m
                    </span>
                  </div>

                  {task.escalated && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1 animate-pulse">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-700" />
                      ESCALATED
                    </span>
                  )}
                </div>

                {/* Card Title */}
                <h3 className="text-base font-bold text-slate-900 leading-snug">
                  {task.title}
                </h3>

                {/* One line clinical reason */}
                <p className="text-xs text-slate-600 mt-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100 font-medium">
                  {task.reason}
                </p>
              </div>

              {/* Action Buttons: Done / Not Useful */}
              <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                <button
                  onClick={() => onAction(task.id, 'not-useful')}
                  className="px-3 py-2 rounded-xl text-xs font-medium text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition flex items-center gap-1 active:scale-95"
                  title="Mark as not useful / dismiss"
                >
                  <X className="w-3.5 h-3.5 text-slate-400" />
                  <span>Not useful</span>
                </button>

                <button
                  onClick={() => onAction(task.id, 'done')}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white shadow-sm transition flex items-center gap-1.5 active:scale-95"
                  title="Mark task completed"
                >
                  <Check className="w-4 h-4" />
                  <span>Done</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
