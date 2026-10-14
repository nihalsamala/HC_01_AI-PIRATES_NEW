import React from 'react';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  unit?: string;
  label?: string;
  currentValue?: number | string | null;
  isFocus?: boolean;
  baselineBand?: { median: number; spread: number };
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  width = 120,
  height = 36,
  color = '#0d9488', // teal-600
  unit = '',
  label = '',
  currentValue,
  isFocus = false,
  baselineBand,
}) => {
  const validData = data.filter((v) => v !== null && !isNaN(v));

  if (validData.length < 2) {
    return (
      <div
        className={`flex items-center justify-between text-xs py-1.5 px-2 rounded-lg ${
          isFocus ? 'bg-amber-50/70 border border-amber-200/80 font-medium' : ''
        }`}
      >
        <div className="flex items-center gap-1.5">
          <span className={`font-semibold ${isFocus ? 'text-amber-950 font-black' : 'text-slate-500'}`}>
            {label}
          </span>
          {isFocus && (
            <span className="text-[9px] font-black uppercase tracking-wider px-1 py-0.2 rounded bg-amber-200/90 text-amber-900 border border-amber-300">
              FOCUS
            </span>
          )}
        </div>
        <span className="text-slate-400 font-mono">
          {currentValue !== null && currentValue !== undefined ? `${currentValue} ${unit}` : 'No data'}
        </span>
      </div>
    );
  }

  let min = Math.min(...validData);
  let max = Math.max(...validData);

  if (baselineBand) {
    min = Math.min(min, baselineBand.median - baselineBand.spread);
    max = Math.max(max, baselineBand.median + baselineBand.spread);
  }

  const range = max - min || 1;
  const padding = 4;
  const graphWidth = width - padding * 2;
  const graphHeight = height - padding * 2;

  const getY = (val: number) => height - padding - ((val - min) / range) * graphHeight;

  const points = validData.map((val, idx) => {
    const x = padding + (idx / (validData.length - 1)) * graphWidth;
    const y = getY(val);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const pathD = `M ${points.join(' L ')}`;
  const latest = validData[validData.length - 1];

  // Shaded baseline band (median +/- spread)
  let bandElement = null;
  if (baselineBand) {
    const topY = getY(baselineBand.median + baselineBand.spread);
    const bottomY = getY(baselineBand.median - baselineBand.spread);
    const bandY = Math.min(topY, bottomY);
    const bandHeight = Math.max(2, Math.abs(bottomY - topY));

    bandElement = (
      <rect
        x={padding}
        y={bandY}
        width={graphWidth}
        height={bandHeight}
        fill={isFocus ? color : '#94a3b8'}
        fillOpacity={isFocus ? 0.22 : 0.12}
        rx={2}
      />
    );
  }

  return (
    <div
      className={`flex items-center justify-between py-1.5 px-2 rounded-xl border-b border-slate-100 last:border-b-0 transition-all ${
        isFocus
          ? 'bg-amber-50/80 border border-amber-200/90 shadow-2xs font-semibold'
          : 'hover:bg-slate-50/50'
      }`}
    >
      <div className="w-24">
        <div className="flex items-center gap-1">
          <span className={`text-xs font-bold block ${isFocus ? 'text-amber-950 font-black' : 'text-slate-700'}`}>
            {label}
          </span>
          {isFocus && (
            <span className="text-[9px] font-black uppercase tracking-wider px-1 py-0.2 rounded bg-amber-200/90 text-amber-900 border border-amber-300">
              FOCUS
            </span>
          )}
        </div>
        <span className={`text-xs font-mono font-bold ${isFocus ? 'text-amber-950 font-black' : 'text-slate-900'}`}>
          {currentValue !== null && currentValue !== undefined ? currentValue : latest}{' '}
          <span className="text-[10px] text-slate-400 font-normal">{unit}</span>
        </span>
      </div>

      <svg width={width} height={height} className="overflow-visible">
        {/* Shaded baseline band behind sparkline */}
        {bandElement}

        {/* Subtle trend line */}
        <path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth={isFocus ? '2.5' : '2'}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Latest point circle */}
        {points.length > 0 && (
          <circle
            cx={points[points.length - 1].split(',')[0]}
            cy={points[points.length - 1].split(',')[1]}
            r={isFocus ? '4' : '3'}
            fill={color}
          />
        )}
      </svg>
    </div>
  );
};
