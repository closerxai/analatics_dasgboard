'use client';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const SLOTS = ['9am', '11', '1pm', '3', '5', '7', '9pm'];

function seed(d: number, h: number): number {
  return ((d * 7 + h * 3 + d * h) * 1103515245 + 12345) & 0x7fffffff;
}

function heatValue(di: number, hi: number): number {
  let v = (seed(di, hi) % 100) / 20 | 0;
  if (di < 5 && hi >= 3 && hi <= 5) v = Math.min(5, v + 2);
  if (di >= 5 && (hi === 2 || hi === 3)) v = Math.min(5, v + 2);
  if (di >= 5 && hi <= 1) v = Math.max(0, v - 1);
  return v;
}

export default function Heatmap() {
  return (
    <div>
      <div className="heat">
        <div />
        {SLOTS.map(s => <div key={s} className="heat-label">{s}</div>)}
        {DAYS.map((day, di) => (
          <>
            <div key={day} className="heat-label">{day}</div>
            {SLOTS.map((_, hi) => {
              const v = heatValue(di, hi);
              return (
                <div
                  key={hi}
                  className="heat-cell"
                  data-v={v}
                  title={`${day} ${SLOTS[hi]} · ${v * 12 + 22}% answered`}
                />
              );
            })}
          </>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, alignItems: 'center' }}>
        <span className="hint">Low</span>
        <div style={{ display: 'flex', gap: 3 }}>
          {[0, 1, 2, 3, 4, 5].map(v => (
            <div key={v} className="heat-cell" data-v={v} style={{ width: 14, height: 10 }} />
          ))}
        </div>
        <span className="hint">High</span>
      </div>
    </div>
  );
}
