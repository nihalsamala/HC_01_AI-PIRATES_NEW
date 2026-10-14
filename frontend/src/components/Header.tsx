import React from 'react';
import { Activity, Play, Pause, RotateCcw, Clock, ShieldAlert, Cpu, Sparkles, MonitorUp } from 'lucide-react';
import { SimState } from '../types';
import { USE_MOCK } from '../api/client';

interface HeaderProps {
  simState: SimState;
  onControl: (action: 'play' | 'pause' | 'reset' | 'set_speed', speed?: number) => void;
  onOpenHelp: () => void;
  onStartDemo: () => void;
  isProjectorMode: boolean;
  onToggleProjectorMode: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  simState,
  onControl,
  onOpenHelp,
  onStartDemo,
  isProjectorMode,
  onToggleProjectorMode,
}) => {
  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return (
        d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) +
        ' (' +
        d.toLocaleDateString([], { month: 'short', day: 'numeric' }) +
        ')'
      );
    } catch {
      return isoString;
    }
  };

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Subtitle */}
        <div className="flex items-center space-x-3">
          <div className="bg-teal-500 text-slate-950 p-2 rounded-xl shadow-inner flex items-center justify-center">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white m-0">WardPulse</h1>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-teal-900/80 text-teal-300 border border-teal-700/50">
                v1.0
              </span>
              {USE_MOCK ? (
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-1">
                  <Cpu className="w-3 h-3" /> MOCK DATA
                </span>
              ) : (
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1">
                  LIVE API
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-medium tracking-wide">
              Early warning decision support • <span className="text-slate-300">Decision support, not diagnosis</span>
            </p>
          </div>
        </div>

        {/* Simulation Clock Controls */}
        <div className="flex items-center flex-wrap gap-2 bg-slate-800/80 px-3 py-1.5 rounded-xl border border-slate-700/60 shadow-inner">
          <div className="flex items-center text-xs font-mono text-slate-300 gap-1.5 pr-2 border-r border-slate-700">
            <Clock className="w-4 h-4 text-teal-400" />
            <span className="font-semibold text-teal-300">{formatTime(simState.sim_time)}</span>
            <span
              className={`inline-block w-2 h-2 rounded-full ml-1 ${
                simState.running ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'
              }`}
              title={simState.running ? 'Clock running' : 'Clock paused'}
            />
          </div>

          {/* Play/Pause */}
          <button
            onClick={() => onControl(simState.running ? 'pause' : 'play')}
            className={`p-1.5 rounded-lg text-xs font-medium flex items-center gap-1 transition ${
              simState.running
                ? 'bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/40'
                : 'bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/40'
            }`}
            title={simState.running ? 'Pause simulation' : 'Play simulation'}
          >
            {simState.running ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{simState.running ? 'Pause' : 'Play'}</span>
          </button>

          {/* Speed Selector */}
          <div className="flex items-center gap-1 text-xs text-slate-400 pl-1">
            <span>Speed:</span>
            {[1, 5, 10, 30].map((s) => (
              <button
                key={s}
                onClick={() => onControl('set_speed', s)}
                className={`px-1.5 py-0.5 rounded text-xs font-mono transition ${
                  simState.speed_minutes_per_second === s
                    ? 'bg-teal-500 text-slate-950 font-bold'
                    : 'text-slate-300 hover:bg-slate-700'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Reset */}
          <button
            onClick={() => onControl('reset')}
            className="p-1.5 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-slate-700 transition"
            title="Reset simulation to 06:00"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Action Group: Demo Mode, Projector, Help */}
        <div className="flex items-center flex-wrap gap-2">
          {/* One-Click Guided Demo Button */}
          <button
            onClick={onStartDemo}
            className="text-xs bg-gradient-to-r from-teal-500 to-emerald-400 hover:from-teal-400 hover:to-emerald-300 text-slate-950 font-extrabold px-3.5 py-1.5 rounded-xl shadow-md flex items-center gap-1.5 transition active:scale-95"
            title="Launch guided walkthrough of the 3 clinical stories"
          >
            <Sparkles className="w-3.5 h-3.5 text-slate-950" />
            <span>Guided Demo</span>
          </button>

          {/* Projector / Large Text Mode Toggle */}
          <button
            onClick={onToggleProjectorMode}
            className={`text-xs px-3 py-1.5 rounded-xl border flex items-center gap-1.5 transition ${
              isProjectorMode
                ? 'bg-amber-400 text-slate-950 font-bold border-amber-300'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
            }`}
            title="Toggle high-contrast projector font sizing"
          >
            <MonitorUp className="w-3.5 h-3.5" />
            <span>{isProjectorMode ? 'Standard Text' : 'Projector Text'}</span>
          </button>

          {/* Clinical Info Button */}
          <button
            onClick={onOpenHelp}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700 flex items-center gap-1.5 transition"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-teal-400" />
            <span>How it works</span>
          </button>
        </div>
      </div>
    </header>
  );
};
