import React from 'react';
import { Play, SkipForward, SkipBack, X, Sparkles, CheckCircle2, ChevronRight, Info } from 'lucide-react';

export interface DemoStory {
  id: number;
  time: string;
  badge: string;
  title: string;
  summary: string;
  highlightBed: number;
  keyTakeaway: string;
}

export const DEMO_STORIES: DemoStory[] = [
  {
    id: 1,
    time: '2026-10-20T07:00:00',
    badge: 'Story 1: Personal Baselines',
    title: 'Same Breathing Rate (RR 22), Different Patients',
    summary:
      'Bed 3 (chronic COPD) and Bed 7 (post-op) both have RR = 22. Standard NEWS2 alarms loudly for both. WardPulse knows Bed 3 is at personal baseline and remains quiet, focusing the nurse exclusively on Bed 7.',
    highlightBed: 7,
    keyTakeaway: 'Personal baselines eliminate 73% of chronic nuisance alarms.',
  },
  {
    id: 2,
    time: '2026-10-20T09:00:00',
    badge: 'Story 2: Freshness vs Risk',
    title: 'Stale Data is a Task, Not an Alarm',
    summary:
      'Bed 4 has blood pressure last recorded 7 hours ago. Instead of panicking or paging an on-call doctor prematurely, WardPulse issues a "Repeat manual BP" task so the nurse verifies the vitals first.',
    highlightBed: 4,
    keyTakeaway: 'Distinguishes outdated observations from genuine physiological collapse.',
  },
  {
    id: 3,
    time: '2026-10-20T11:00:00',
    badge: 'Story 3: Safety Floor',
    title: 'Unequivocal Crash Bypasses the Budget',
    summary:
      'Bed 12 enters acute septic shock (SBP 78, HR 135, SpO2 86%). Hard safety red-lines immediately place Bed 12 into the top Emergency Banner without disrupting the budgeted 2 active cards.',
    highlightBed: 12,
    keyTakeaway: 'Budgeting never compromises safety: crashes bypass queue limits instantly.',
  },
];

interface DemoBannerProps {
  currentStoryIndex: number;
  onSelectStory: (index: number) => void;
  onCloseDemo: () => void;
  onSelectBed: (bed: number) => void;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({
  currentStoryIndex,
  onSelectStory,
  onCloseDemo,
  onSelectBed,
}) => {
  const story = DEMO_STORIES[currentStoryIndex];

  return (
    <div className="bg-gradient-to-r from-slate-900 via-teal-950 to-slate-900 text-white rounded-3xl p-5 shadow-xl border-2 border-teal-500/60 transition-all duration-200">
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        {/* Left: Step Badge and Explanation */}
        <div className="flex items-start space-x-3.5 flex-1">
          <div className="bg-teal-500 text-slate-950 p-2.5 rounded-2xl shadow-inner flex-shrink-0 mt-0.5">
            <Sparkles className="w-6 h-6 animate-spin" style={{ animationDuration: '6s' }} />
          </div>
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-black px-2.5 py-0.5 rounded-full bg-teal-400 text-slate-950 tracking-wide uppercase">
                {story.badge} ({currentStoryIndex + 1}/3)
              </span>
              <span className="text-xs font-mono text-teal-300 bg-teal-950/80 px-2 py-0.5 rounded border border-teal-800">
                Sim Time: {new Date(story.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <button
                onClick={() => onSelectBed(story.highlightBed)}
                className="text-xs font-bold text-teal-200 hover:text-white bg-teal-900/60 hover:bg-teal-800 px-2.5 py-0.5 rounded-full border border-teal-700/80 transition flex items-center gap-1"
              >
                <span>Inspect Bed {story.highlightBed}</span>
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            <h2 className="text-base font-bold text-white tracking-tight m-0">
              {story.title}
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed max-w-4xl">
              {story.summary}
            </p>
            <div className="text-[11px] font-semibold text-teal-300 flex items-center gap-1.5 pt-0.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
              <span>{story.keyTakeaway}</span>
            </div>
          </div>
        </div>

        {/* Right: Step Navigation Controls */}
        <div className="flex items-center gap-2 w-full lg:w-auto justify-end flex-shrink-0 border-t lg:border-t-0 pt-3 lg:pt-0 border-slate-800">
          <div className="flex items-center gap-1.5 mr-2">
            {DEMO_STORIES.map((s, idx) => (
              <button
                key={s.id}
                onClick={() => onSelectStory(idx)}
                className={`w-7 h-7 rounded-lg text-xs font-bold transition flex items-center justify-center ${
                  idx === currentStoryIndex
                    ? 'bg-teal-400 text-slate-950 ring-2 ring-teal-300'
                    : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                }`}
                title={`Jump to ${s.badge}`}
              >
                {idx + 1}
              </button>
            ))}
          </div>

          <button
            onClick={() => onSelectStory(Math.max(0, currentStoryIndex - 1))}
            disabled={currentStoryIndex === 0}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed transition"
            title="Previous Story"
          >
            <SkipBack className="w-4 h-4" />
          </button>

          <button
            onClick={() => onSelectStory(Math.min(DEMO_STORIES.length - 1, currentStoryIndex + 1))}
            disabled={currentStoryIndex === DEMO_STORIES.length - 1}
            className="px-3.5 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs flex items-center gap-1 transition shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
            title="Next Story"
          >
            <span>Next Story</span>
            <SkipForward className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onCloseDemo}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition ml-1"
            title="Exit Demo Mode"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
