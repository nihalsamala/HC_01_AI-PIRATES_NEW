import React, { useState } from 'react';
import {
  Activity,
  Play,
  Pause,
  ChevronDown,
  Moon,
  Sun,
  User,
} from 'lucide-react';
import { Mode, SimState } from '../types';

interface TopBarProps {
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  simState: SimState;
  onSimControl: (action: 'play' | 'pause' | 'reset' | 'set_speed', speed?: number) => void;
  budgetK: number;
  onBudgetKChange: (k: number) => void;
  isProjectorMode?: boolean;
  onToggleProjectorMode?: () => void;
  dataSourceLabel?: string;
}

export const TopBar: React.FC<TopBarProps> = ({
  mode,
  onModeChange,
  simState,
  onSimControl,
  budgetK,
  onBudgetKChange,
  isProjectorMode = false,
  onToggleProjectorMode,
  dataSourceLabel,
}) => {
  const [selectedLang, setSelectedLang] = useState<'EN' | 'हिं' | 'తె'>('EN');
  const [speedDropdownOpen, setSpeedDropdownOpen] = useState(false);

  // Format sim time as HH:MM
  let formattedTime = '02:30';
  let shiftLabel = 'Day 2 · night shift';

  try {
    const d = new Date(simState.sim_time);
    if (!isNaN(d.getTime())) {
      const hours = d.getHours().toString().padStart(2, '0');
      const minutes = d.getMinutes().toString().padStart(2, '0');
      formattedTime = `${hours}:${minutes}`;

      const h = d.getHours();
      let shift = 'night shift';
      if (h >= 7 && h < 15) shift = 'day shift';
      else if (h >= 15 && h < 23) shift = 'evening shift';

      const startMs = new Date('2026-10-20T00:00:00').getTime();
      const currentMs = d.getTime();
      const dayNum = Math.max(1, Math.floor((currentMs - startMs) / 86400000) + 1);
      shiftLabel = `Day ${dayNum} · ${shift}`;
    }
  } catch {
    // fallback
  }

  const speedOptions = [
    { label: '1× (Realtime)', value: 1.0 },
    { label: '10×', value: 10.0 },
    { label: '60×', value: 60.0 },
    { label: '300×', value: 300.0 },
  ];

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 flex items-center justify-between select-none shrink-0 z-30 shadow-xs">
      {/* Left: Logo & Ward Description */}
      <div className="flex items-center gap-4">
        {/* Brand Icon & Name */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-xs">
            <Activity className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-slate-900 text-base tracking-tight leading-none">
              WardPulse
            </span>
            <span className="text-[11px] font-semibold text-slate-500 leading-tight mt-0.5">
              Nurse Attention Allocator
            </span>
          </div>
        </div>

        {/* Ward Location Tag */}
        <div className="hidden xl:flex flex-col border-l border-slate-200 pl-4 py-0.5">
          <span className="text-xs font-bold text-slate-800 leading-tight">
            Ward 3B · General Medicine &amp; Surgery
          </span>
        </div>
      </div>

      {/* Center: Naïve AI vs WardPulse Mode Toggle */}
      <div className="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200/80">
        <button
          onClick={() => onModeChange('news2')}
          className={`flex flex-col items-center px-4 py-1.5 rounded-xl text-xs transition-all ${
            mode === 'news2'
              ? 'bg-white text-rose-700 shadow-xs font-bold border border-rose-200/60'
              : 'text-slate-600 hover:text-slate-900 font-medium'
          }`}
          title="Naïve AI mode: traditional NEWS2 threshold alerts with noise and alarm fatigue"
        >
          <span className="leading-tight font-bold">Naïve AI</span>
          <span className="text-[10px] text-slate-600 font-medium leading-tight">threshold alarms</span>
        </button>

        <button
          onClick={() => onModeChange('wardpulse')}
          className={`flex flex-col items-center px-4 py-1.5 rounded-xl text-xs transition-all ${
            mode === 'wardpulse'
              ? 'bg-teal-600 text-white shadow-sm font-bold'
              : 'text-slate-600 hover:text-slate-900 font-medium'
          }`}
          title="WardPulse mode: bounded K-attention budget, personalised baselines, and prioritized queue"
        >
          <span className="leading-tight font-bold">WardPulse</span>
          <span className="text-[10px] text-teal-100/90 font-medium leading-tight">K-card budget</span>
        </button>
      </div>

      {/* Right Controls: Sim Clock + K Selector + Profile */}
      <div className="flex items-center gap-3">
        {/* Simulation Clock Controls */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-xl">
          <button
            onClick={() => onSimControl(simState.running ? 'pause' : 'play')}
            className="w-7 h-7 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 flex items-center justify-center text-slate-700 transition shadow-2xs"
            title={simState.running ? 'Pause simulation' : 'Play simulation'}
          >
            {simState.running ? (
              <Pause className="w-3.5 h-3.5 fill-slate-700" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-slate-700 translate-x-0.5" />
            )}
          </button>

          <div className="flex flex-col items-center px-1">
            <span className="font-mono text-sm font-black text-slate-800 tracking-tight leading-none">
              {formattedTime}
            </span>
            <span className="text-[10px] text-slate-600 font-medium leading-tight mt-0.5">
              {shiftLabel}
            </span>
          </div>

          {/* Speed Selector */}
          <div className="relative">
            <button
              onClick={() => setSpeedDropdownOpen(!speedDropdownOpen)}
              className="flex items-center gap-1 text-xs font-semibold bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 px-2 py-1 rounded-lg transition"
            >
              <span>{Math.round(simState.speed_minutes_per_second)}×</span>
              <ChevronDown className="w-3 h-3 text-slate-600" />
            </button>

            {speedDropdownOpen && (
              <div className="absolute right-0 top-full mt-1.5 w-32 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-50">
                {speedOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => {
                      onSimControl('set_speed', opt.value);
                      setSpeedDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 text-xs font-medium hover:bg-teal-50 ${
                      Math.round(simState.speed_minutes_per_second) === opt.value
                        ? 'text-teal-700 font-bold bg-teal-50/60'
                        : 'text-slate-700'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* K Selector (Attention Budget 1, 2, 3) */}
        <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 px-2 py-1 rounded-xl">
          <span className="text-xs font-black text-slate-600 mr-1 italic">K</span>
          {[1, 2, 3].map((kVal) => (
            <button
              key={kVal}
              onClick={() => onBudgetKChange(kVal)}
              className={`w-6 h-6 rounded-lg text-xs font-black transition-all ${
                budgetK === kVal
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200'
              }`}
            >
              {kVal}
            </button>
          ))}
        </div>

        {/* Language Switcher */}
        <div className="hidden lg:flex items-center bg-slate-50 border border-slate-200 p-0.5 rounded-xl">
          {(['EN', 'हिं', 'తె'] as const).map((lang) => (
            <button
              key={lang}
              onClick={() => setSelectedLang(lang)}
              className={`px-2 py-1 rounded-lg text-xs font-semibold transition ${
                selectedLang === lang
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-800'
              }`}
            >
              {lang}
            </button>
          ))}
        </div>

        {/* Dark / Projector Mode Toggle */}
        <button
          onClick={onToggleProjectorMode}
          className="w-8 h-8 rounded-xl border border-slate-200 bg-white hover:bg-slate-100 flex items-center justify-center text-slate-600 transition"
          title={isProjectorMode ? 'Disable projector mode' : 'Enable projector / high-contrast mode'}
        >
          {isProjectorMode ? (
            <Sun className="w-4 h-4 text-amber-500" />
          ) : (
            <Moon className="w-4 h-4" />
          )}
        </button>

        {/* Nurse User Profile */}
        <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 pl-2 pr-3 py-1 rounded-xl text-xs font-bold text-slate-800">
          <div className="w-5 h-5 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center">
            <User className="w-3 h-3" />
          </div>
          <span>Sr. Anjali</span>
          <ChevronDown className="w-3 h-3 text-slate-600" />
        </div>
      </div>
    </header>
  );
};
