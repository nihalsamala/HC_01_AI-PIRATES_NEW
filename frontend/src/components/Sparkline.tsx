import React from 'react';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  unit?: string;
  label?: string;
  currentValue?: number | string | null;
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  width = 120,
  height = 36,
  color = '#0d9488', // teal-600
  unit = '',
  label = '',
  currentValue,
}) => {
  const validData = data.filter((v) => v !== null && !isNaN(v));

  if (validData.length < 2) {
    return (
      <div className="flex items-center justify-between text-xs py-1">
        <span className="text-slate-500 font-medium">{label}</span>
        <span className="text-slate-400 font-mono">
          {currentValue !== null && currentValue !== undefined ? `${currentValue} ${unit}` : 'No data'}
        </span>
      </div>
    );
  }

  const min = Math.min(...validData);
  const max = Math.max(...validData);
  const range = max - min || 1;

  const padding = 4;
  const graphWidth = width - padding * 2;
  const graphHeight = height - padding * 2;

  const points = validData.map((val, idx) => {
    const x = padding + (idx / (validData.length - 1)) * graphWidth;
    const y = height - padding - ((val - min) / range) * graphHeight;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const pathD = `M ${points.join(' L ')}`;
  const latest = validData[validData.length - 1];

  return (
    <div className="flex items-center justify-between py-1 border-b border-slate-100 last:border-b-0">
      <div className="w-20">
        <span className="text-xs font-semibold text-slate-700 block">{label}</span>
        <span className="text-xs font-mono font-bold text-slate-900">
          {currentValue !== null && currentValue !== undefined ? currentValue : latest}{' '}
          <span className="text-[10px] text-slate-400 font-normal">{unit}</span>
        </span>
      </div>

      <svg width={width} height={height} className="overflow-visible">
        {/* Subtle trend line */}
        <path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Latest point circle */}
        {points.length > 0 && (
          <circle
            cx={points[points.length - 1].split(',')[0]}
            cy={points[points.length - 1].split(',')[1]}
            r="3"
            fill={color}
          />
        )}
      </svg>
    </div>
  );
};
