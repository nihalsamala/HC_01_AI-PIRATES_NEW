import React from 'react';
import { History, Play, Check } from 'lucide-react';
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
    id: 'calm',
    timeLabel: '14:00',
    title: 'Calm ward',
    fullTime: '2026-10-20T14:00:00',
    bed: 1,
    description: 'Routine general medicine ward: 20 beds stable, no active attention cards required.',
  },
  {
    id: 'cannula',
    timeLabel: '01:15',
    title: 'Bed 9 cannula',
    fullTime: '2026-10-21T01:15:00',
    bed: 9,
    description: 'Bed 9 COPD oxygen saturation drop: cannula displacement detected before severe hypoxemia.',
  },
  {
    id: 'overflow',
    timeLabel: '02:30',
    title: 'Budget overflow',
    fullTime: '2026-10-21T02:30:00',
    bed: 7,
    description: 'Multiple deterioration signals: top 2 critical actions presented, remaining held in ranked standby queue.',
  },
  {
    id: 'drifting',
    timeLabel: '10:30',
    title: 'Bed 12 drifting',
    fullTime: '2026-10-21T10:30:00',
    bed: 12,
    description: 'Post-op patient subtle drift vs personal baseline: respiratory rate rising from 14 to 22.',
  },
  {
    id: 'crash',
    timeLabel: '14:03',
    title: 'Bed 12 crash',
    fullTime: '2026-10-21T14:03:00',
    bed: 12,
    description: 'Crash bypass activation: instant emergency banner alerts doctor for Bed 12 septic shock.',
  },
];

interface ReplayTimelineProps {
  simState: SimState;
  activeStoryId: string;
  onSelectStory: (story: DemoStory) => void;
}

export const ReplayTimeline: React.FC<ReplayTimelineProps> = ({
  simState,
  activeStoryId,
  onSelectStory,
}) => {
  const tickMarks = [
    '08:00',
    '12:00',
    '16:00',
    '20:00',
    '00:00',
    '04:00',
    '08:00',
    '12:00',
    '16:00',
    '20:00',
    '00:00',
    '04:00',
    '08:00',
  ];

  return (
    <footer className="h-16 bg-white border-t border-slate-200 px-4 flex items-center justify-between select-none shrink-0 z-20 shadow-xs">
      {/* Left: Replay Label */}
      <div className="flex items-center gap-2 mr-3 shrink-0">
        <span className="text-[11px] font-black uppercase tracking-wider text-slate-500">
          REPLAY
        </span>
      </div>

      {/* Center: Track with Tick Marks & Scrubber Markers */}
      <div className="flex-1 max-w-2xl hidden md:flex flex-col justify-center px-4">
        {/* Scrubber Track */}
        <div className="relative h-2 bg-slate-100 rounded-full flex items-center">
          {/* Progress bar up to current position */}
          <div
            className="absolute left-0 top-0 bottom-0 bg-teal-500 rounded-full"
            style={{ width: '45%' }}
          />

          {/* Scrubber Thumb */}
          <div
            className="absolute w-4 h-4 rounded-full bg-teal-600 border-2 border-white shadow-md cursor-pointer hover:scale-110 transition-transform"
            style={{ left: '44%' }}
          />

          {/* Event Dots along the track */}
          <span className="absolute left-[20%] w-2 h-2 rounded-full border border-teal-600 bg-white" />
          <span className="absolute left-[40%] w-2 h-2 rounded-full border border-teal-600 bg-white" />
          <span className="absolute left-[43%] w-2.5 h-2.5 rotate-45 border border-rose-500 bg-rose-100" />
          <span className="absolute left-[58%] w-2 h-2 rounded-full border border-teal-600 bg-white" />
          <span className="absolute left-[65%] w-2.5 h-2.5 rotate-45 border border-amber-500 bg-amber-100" />
          <span className="absolute left-[78%] w-2.5 h-2.5 rotate-45 border border-rose-600 bg-rose-500" />
        </div>

        {/* Time Ticks */}
        <div className="flex justify-between text-[9px] font-mono text-slate-400 mt-1">
          {tickMarks.map((tick, idx) => (
            <span key={idx}>{tick}</span>
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
              className={`px-2.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                isActive
                  ? 'bg-teal-50 border border-teal-600 text-teal-900 font-bold shadow-2xs'
                  : 'bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-600'
              }`}
              title={story.description}
            >
              <span className="font-mono text-[11px] text-slate-400 font-normal">
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
