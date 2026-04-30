'use client';

import { useMemo } from 'react';
import { getSourceColor } from '@/lib/types';

interface DonutSlice {
  name: string;
  n: number;
  color?: string;
}

interface Props {
  data: DonutSlice[];
  total?: number;
}

export default function DonutChart({ data, total }: Props) {
  const sum = total ?? data.reduce((a, b) => a + b.n, 0);

  const paths = useMemo(() => {
    const cx = 60, cy = 60, r = 44, sw = 14;
    let a0 = -Math.PI / 2;
    return data.map(s => {
      const color = s.color || getSourceColor(s.name);
      const a1 = a0 + (s.n / sum) * Math.PI * 2;
      const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
      const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
      const large = (a1 - a0) > Math.PI ? 1 : 0;
      const d = `M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`;
      a0 = a1;
      return { d, color, name: s.name, n: s.n, pct: s.n / sum * 100, sw };
    });
  }, [data, sum]);

  if (!data.length) return null;

  return (
    <div className="donut-wrap">
      <div style={{ position: 'relative', width: 170, height: 170 }}>
        <svg viewBox="0 0 120 120" style={{ width: '100%', height: '100%' }}>
          {paths.map(p => (
            <path key={p.name} d={p.d} fill="none" stroke={p.color} strokeWidth={p.sw} strokeLinecap="butt">
              <title>{p.name} · {p.n} leads · {p.pct.toFixed(1)}%</title>
            </path>
          ))}
          <circle cx="60" cy="60" r="44" fill="none" stroke="var(--line)" strokeWidth="1" strokeDasharray="2 3" opacity="0.4" />
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', textAlign: 'center' }}>
          <div>
            <div className="mono" style={{ fontSize: 24, fontWeight: 600, letterSpacing: -0.02 }}>
              {sum.toLocaleString()}
            </div>
            <div className="muted" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Total leads
            </div>
          </div>
        </div>
      </div>
      <div className="donut-legend">
        {data.map(s => {
          const color = s.color || getSourceColor(s.name);
          const pct = (s.n / sum * 100).toFixed(1);
          return (
            <div key={s.name} className="leg-row">
              <span className="swatch" style={{ background: color }} />
              <span>{s.name}</span>
              <span className="n mono">{s.n}</span>
              <span className="pct mono">{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
