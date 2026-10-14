import React from 'react';
import { Task } from '../types';
import { AlertOctagon, CheckCircle2, ChevronRight, PhoneCall } from 'lucide-react';
import { formatCardReason } from '../utils/reasons';

interface EmergencyBannerProps {
  emergencyTasks: Task[];
  onAction: (taskId: number, action: 'done' | 'not-useful') => void;
  onSelectBed: (bed: number) => void;
}

export const EmergencyBanner: React.FC<EmergencyBannerProps> = ({
  emergencyTasks,
  onAction,
  onSelectBed,
}) => {
  if (!emergencyTasks || emergencyTasks.length === 0) return null;

  return (
    <div className="space-y-3">
      {emergencyTasks.map((task) => (
        <div
          key={task.id}
          className="bg-rose-600 text-white rounded-2xl p-4 sm:p-5 shadow-lg border-2 border-rose-400 pulse-emergency flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
        >
          {/* Emergency Alert Tag & Description */}
          <div className="flex items-start space-x-3.5">
            <div className="bg-white/20 p-2.5 rounded-xl text-white shadow-inner flex-shrink-0 animate-bounce">
              <AlertOctagon className="w-7 h-7" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="bg-white text-rose-900 text-xs font-black px-2.5 py-0.5 rounded-md uppercase tracking-wider">
                  EMERGENCY BYPASS
                </span>
                <span className="text-white font-bold text-lg">
                  BED {task.bed} • {task.title}
                </span>
                <span className="text-xs font-mono bg-rose-900/60 text-rose-200 px-2 py-0.5 rounded">
                  Waited {Math.round(task.waiting_minutes)}m
                </span>
              </div>
              <p className="text-rose-100 text-sm mt-1 font-medium max-w-3xl">
                {formatCardReason(task.reason, task.title)}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 w-full md:w-auto justify-end flex-shrink-0">
            <button
              onClick={() => onSelectBed(task.bed)}
              className="px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold flex items-center gap-1 transition border border-white/20"
            >
              <span>View Patient</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onAction(task.id, 'done')}
              className="px-4 py-2 rounded-xl bg-white hover:bg-rose-50 text-rose-900 font-bold text-xs flex items-center gap-1.5 shadow-sm transition active:scale-95"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Acknowledged / Done</span>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
