'use client';

import { useEffect, useState } from 'react';
import Topbar from '@/components/layout/Topbar';
import { getSourceWise, getProjects } from '@/lib/api';
import { LEAD_STATUS_LABELS, LeadStatus, getSourceColor } from '@/lib/types';

const DEFAULT_COLS: LeadStatus[] = [
  'uncontacted','qualified','disqualified','not_responding',
  'call_back','booked_site_visit','site_visit_done',
];

export default function SourceWisePage() {
  const [projects, setProjects] = useState<{ id: number; name: string }[]>([]);
  const [projectId, setProjectId] = useState('all');
  const [days, setDays] = useState(30);
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [visibleCols, setVisibleCols] = useState<LeadStatus[]>(DEFAULT_COLS);

  useEffect(() => {
    getProjects().then(setProjects).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    getSourceWise(days, projectId === 'all' ? undefined : projectId)
      .then(d => { setRows(d.rows); setTotal(d.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days, projectId]);

  return (
    <>
      <Topbar crumb="Source-wise View">
        <select className="mini-select" value={projectId} onChange={e => setProjectId(e.target.value)}>
          <option value="all">All Projects</option>
          {projects.map(p => <option key={p.id} value={String(p.id)}>{p.name}</option>)}
        </select>
        <div className="seg">
          {[7,30].map(d => (
            <button key={d} className={days === d ? 'on' : ''} onClick={() => setDays(d)}>{d}d</button>
          ))}
          <button>QTD</button><button>YTD</button>
        </div>
      </Topbar>

      <div className="page">
        <div className="page-head">
          <div>
            <h1 className="page-title">Source-wise View</h1>
            <div className="page-sub">Lead counts by source × status · click any number to drill into Leads Insights</div>
          </div>
        </div>

        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Lead Summary by Source</div>
              <div className="card-sub">
                <span className="mono strong">{total.toLocaleString()}</span> total leads · last {days} days
              </div>
            </div>
            <div style={{ display:'flex', gap:8 }}>
              <button className="btn">Export</button>
            </div>
          </div>

          <div className="table-wrap" style={{ maxHeight: 560 }}>
            {loading ? (
              <div style={{ padding:40, textAlign:'center' }}><span className="spinner" /></div>
            ) : rows.length === 0 ? (
              <div className="empty-state">
                <h3>No data yet</h3>
                <p>Sync leads from GHL to see source-wise breakdown</p>
              </div>
            ) : (
              <table className="data">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th style={{ textAlign:'right' }}>Total</th>
                    {visibleCols.map(c => (
                      <th key={c} style={{ textAlign:'right' }}>{LEAD_STATUS_LABELS[c]}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map(row => (
                    <tr key={row.source}>
                      <td>
                        <span className="source-tag">
                          <span className="dot" style={{ background: getSourceColor(row.source) }} />
                          {row.source}
                        </span>
                      </td>
                      <td className="mono strong" style={{ textAlign:'right' }}>
                        {row.total.toLocaleString()}
                      </td>
                      {visibleCols.map(c => (
                        <td key={c} className="mono" style={{ textAlign:'right' }}>
                          {(row.by_status?.[c] || 0).toLocaleString()}
                        </td>
                      ))}
                    </tr>
                  ))}

                  {/* Totals row */}
                  <tr style={{ background:'var(--panel-2)', fontWeight:600 }}>
                    <td><span className="strong">Total</span></td>
                    <td className="mono strong" style={{ textAlign:'right' }}>{total.toLocaleString()}</td>
                    {visibleCols.map(c => {
                      const sum = rows.reduce((a, r) => a + (r.by_status?.[c] || 0), 0);
                      return <td key={c} className="mono" style={{ textAlign:'right' }}>{sum.toLocaleString()}</td>;
                    })}
                  </tr>
                </tbody>
              </table>
            )}
          </div>
        </section>

        {/* Column toggle */}
        <section className="card">
          <div className="card-head">
            <div className="card-title">Visible Columns</div>
          </div>
          <div className="card-body">
            <div className="checkgrid">
              {(Object.keys(LEAD_STATUS_LABELS) as LeadStatus[]).map(col => (
                <label key={col} className="chk" style={{ cursor:'pointer' }}>
                  <input
                    type="checkbox"
                    checked={visibleCols.includes(col)}
                    onChange={e => {
                      setVisibleCols(prev =>
                        e.target.checked ? [...prev, col] : prev.filter(c => c !== col)
                      );
                    }}
                  />
                  <div>
                    <b>{LEAD_STATUS_LABELS[col]}</b>
                    <small>Show in source table</small>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
