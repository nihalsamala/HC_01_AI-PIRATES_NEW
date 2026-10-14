import React from 'react';
import { Task } from '../types';
import { ListOrdered, Clock, ChevronRight } from 'lucide-react';

interface StandbyQueueProps {
  queue: Task[];
  onSelectBed: (bed: number) => void;
}

export const StandbyQueue: React.FC<StandbyQueueProps> = ({ queue, onSelectBed }) => {
  if (!queue || queue.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center gap-2">
          <ListOrdered className="w-4 h-4 text-slate-500" />
          <h3 className="text-sm font-bold text-slate-800 m-0">Standby Queue</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
            {queue.length} in queue
          </span>
        </div>
        <span className="text-xs text-slate-400">
          Ranked by urgency + waiting aging
        </span>
      </div>

      <div className="divide-y divide-slate-100">
        {queue.map((task, idx) => (
          <div
            key={task.id}
            className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50/80 px-2 rounded-xl transition"
          >
            <div className="flex items-start sm:items-center gap-3">
              <span className="w-5 text-xs font-mono font-bold text-slate-400">
                #{idx + 1}
              </span>
              <button
                onClick={() => onSelectBed(task.bed)}
                className="text-xs font-black px-2 py-0.5 rounded-md bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200 transition flex items-center gap-0.5"
              >
                <span>Bed {task.bed}</span>
                <ChevronRight className="w-3 h-3 text-slate-400" />
              </button>
              <div>
                <span className="text-xs font-semibold text-slate-800">
                  {task.title}
                </span>
                <span className="text-xs text-slate-500 block sm:inline sm:ml-2">
                  — {task.reason}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3 self-end sm:self-center">
              <span className="text-xs font-mono text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-400" />
                {Math.round(task.waiting_minutes)}m
              </span>
              <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                score {task.priority.toFixed(1)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
