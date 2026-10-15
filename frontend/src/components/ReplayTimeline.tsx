import React from 'react';
import { History, Play, Check, AlertCircle, Sparkles } from 'lucide-react';
import { SimState } from '../types';

export interface DemoStory {
  id: string;
  timeLabel: string;
  title: string;
  fullTime: string;
  bed: number;
  description: string;
}

export const REPLAY_STORIES: DemoStory[] = [
  {
    id: 'start',
    timeLabel: '06:00',
    title: 'Shift Start',
    fullTime: '2026-10-20T06:00:00',
    bed: 1,
    description: 'Ward handover at 06:00: 20 beds calm/stable, 0 active attention cards required.',
  },
  {
    id: 'story1',
    timeLabel: '07:00',
    title: 'Story 1: COPD vs Post-op',
    fullTime: '2026-10-20T07:00:00',
    bed: 7,
    description: 'Bed 7 post-op acute RR 22 active card, Bed 3 chronic COPD baseline RR 22 calm.',
  },
  {
    id: 'story2',
    timeLabel: '09:00',
    title: 'Story 2: Stale BP check',
    fullTime: '2026-10-20T09:00:00',
    bed: 4,
    description: 'Bed 4 stale BP receives repeat_bp check without triggering false doctor page.',
  },
  {
    id: 'story3',
    timeLabel: '11:00',
    title: 'Story 3: Crash bypass',
    fullTime: '2026-10-20T11:00:00',
    bed: 12,
    description: 'Bed 12 septic shock crash bypasses queue in emergency banner while active holds K=2.',
  },
  {
    id: 'story4',
    timeLabel: '12:00',
    title: 'Story 4: Live Bed 5 COPD',
    fullTime: '2026-10-20T12:00:00',
    bed: 5,
    description: 'Live typed-in COPD hypoxia deterioration on Bed 5 (SpO2 88% despite oxygen).',
  },
];

const SHIFT_START_MS = new Date('2026-10-20T06:00:00').getTime();
const SHIFT_DURATION_MINUTES = 720; // 12 hours (06:00 to 18:00)

interface ReplayTimelineProps {
  simState: SimState;
  activeStoryId: string;
  onSelectStory: (story: DemoStory) => void;
  onSeekTime?: (isoString: string) => void;
}

export const ReplayTimeline: React.FC<ReplayTimelineProps> = ({
  simState,
  activeStoryId,
  onSelectStory,
  onSeekTime,
}) => {
  const tickMarks = [
    { label: '06:00', min: 0 },
    { label: '08:00', min: 120 },
    { label: '10:00', min: 240 },
    { label: '12:00', min: 360 },
    { label: '14:00', min: 480 },
    { label: '16:00', min: 600 },
    { label: '18:00', min: 720 },
  ];

  // Calculate current slider position in minutes from shift start
  const currentSimMs = new Date(simState.sim_time).getTime();
  const rawMinutes = Math.round((currentSimMs - SHIFT_START_MS) / 60000);
  const currentMinutes = Math.max(0, Math.min(SHIFT_DURATION_MINUTES, isNaN(rawMinutes) ? 0 : rawMinutes));
  const progressPercent = Math.min(100, Math.max(0, (currentMinutes / SHIFT_DURATION_MINUTES) * 100));

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const mins = Number(e.target.value);
    const targetMs = SHIFT_START_MS + mins * 60000;
    const targetIso = new Date(targetMs).toISOString().slice(0, 19);
    if (onSeekTime) {
      onSeekTime(targetIso);
    }
  };

  return (
    <footer className="h-16 bg-white border-t border-slate-200 px-4 flex items-center justify-between select-none shrink-0 z-20 shadow-xs gap-3">
      {/* Left: Replay Label & Current Scrubber Time */}
      <div className="flex items-center gap-2 mr-1 shrink-0">
        <span className="text-[11px] font-black uppercase tracking-wider text-teal-700 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded-md">
          REPLAY
        </span>
        <span className="font-mono text-xs font-bold text-slate-700">
          {new Date(simState.sim_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
        </span>
      </div>

      {/* Center: Slideable Scrubber Track with Interactive Slider */}
      <div className="flex-1 max-w-xl hidden md:flex flex-col justify-center px-2">
        {/* Scrubber Container */}
        <div className="relative h-6 flex items-center group">
          {/* Track background */}
          <div className="w-full h-2 bg-slate-100 rounded-full relative overflow-hidden pointer-events-none border border-slate-200/80">
            {/* Progress fill */}
            <div
              className="h-full bg-teal-500 rounded-full transition-all duration-75"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Story marker pins on track */}
          {[
            { min: 60, title: 'Story 1: Bed 7' },
            { min: 180, title: 'Story 2: Bed 4' },
            { min: 300, title: 'Story 3: Bed 12' },
            { min: 360, title: 'Story 4: Bed 5' },
          ].map((pin) => {
            const leftPct = (pin.min / SHIFT_DURATION_MINUTES) * 100;
            return (
              <span
                key={pin.min}
                title={pin.title}
                className="absolute w-2 h-2 -ml-1 rounded-full border border-teal-700 bg-white shadow-2xs pointer-events-none z-10"
                style={{ left: `${leftPct}%` }}
              />
            );
          })}

          {/* Scrubber Thumb Indicator */}
          <div
            className="absolute w-4 h-4 -ml-2 rounded-full bg-teal-600 border-2 border-white shadow-md pointer-events-none transition-all duration-75 z-20 group-hover:scale-110"
            style={{ left: `${progressPercent}%` }}
          />

          {/* Interactive Native Range Input Overlay */}
          <input
            type="range"
            min={0}
            max={SHIFT_DURATION_MINUTES}
            step={5}
            value={currentMinutes}
            onChange={handleSliderChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-30 m-0"
            title="Drag or click to seek simulation timeline"
          />
        </div>

        {/* Time Ticks */}
        <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-0.5 px-0.5">
          {tickMarks.map((tick) => (
            <span key={tick.min}>{tick.label}</span>
          ))}
        </div>
      </div>

      {/* Right: Demo Story Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto py-1">
        {REPLAY_STORIES.map((story) => {
          const isActive = activeStoryId === story.id;

          return (
            <button
              key={story.id}
              onClick={() => onSelectStory(story)}
              className={`px-2.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 cursor-pointer ${
                isActive
                  ? 'bg-teal-50 border border-teal-600 text-teal-900 font-bold shadow-2xs'
                  : 'bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-600'
              }`}
              title={story.description}
            >
              <span className="font-mono text-[11px] text-teal-700 font-bold">
                {story.timeLabel}
              </span>
              <span>{story.title}</span>
            </button>
          );
        })}
      </div>
    </footer>
  );
};
