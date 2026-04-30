'use client';

import { useEffect, useState } from 'react';
import Topbar from '@/components/layout/Topbar';
import { getAgents, getProjects } from '@/lib/api';
import { LEAD_STATUS_LABELS, LeadStatus, getInitials } from '@/lib/types';

const VISIBLE_STATUSES: LeadStatus[] = [
  'uncontacted','qualified','disqualified','not_responding',
  'call_back','booked_site_visit','site_visit_done','whatsapp',
];

export default function SalesAgentsPage() {
  const [projects, setProjects] = useState<{ id: number; name: string }[]>([]);
  const [projectId, setProjectId] = useState('all');
  const [days, setDays] = useState(30);
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { getProjects().then(setProjects).catch(() => {}); }, []);

  useEffect(() => {
    setLoading(true);
    getAgents(days, projectId === 'all' ? undefined : projectId)
      .then(d => setAgents(d.agents))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days, projectId]);

  return (
    <>
      <Topbar crumb="Sales Agent View">
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
        <button className="btn primary">Export</button>
      </Topbar>

      <div className="page">
        <div className="page-head">
          <div>
            <h1 className="page-title">Sales Agent View</h1>
            <div className="page-sub">Response counts by status across agents · last {days} days</div>
          </div>
        </div>

        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Agent Breakdown</div>
              <div className="card-sub">Click a cell to drill into Leads Insights</div>
            </div>
          </div>
          <div className="table-wrap" style={{ maxHeight:620 }}>
            {loading ? (
              <div style={{ padding:40, textAlign:'center' }}><span className="spinner" /></div>
            ) : agents.length === 0 ? (
              <div className="empty-state">
                <h3>No agent data yet</h3>
                <p>Leads assigned to agents will appear here after syncing</p>
              </div>
            ) : (
              <table className="data">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th style={{ textAlign:'right' }}>Total</th>
                    {VISIBLE_STATUSES.map(s => (
                      <th key={s} style={{ textAlign:'right' }}>{LEAD_STATUS_LABELS[s]}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {agents.map(row => (
                    <tr key={row.agent}>
                      <td>
                        <div className="contact-cell">
                          <div className="avatar">{getInitials(row.agent)}</div>
                          <div>
                            <div className="contact-name">{row.agent}</div>
                          </div>
                        </div>
                      </td>
                      <td className="mono strong" style={{ textAlign:'right' }}>
                        {row.total.toLocaleString()}
                      </td>
                      {VISIBLE_STATUSES.map(s => (
                        <td key={s} className="mono" style={{ textAlign:'right' }}>
                          {(row.by_status?.[s] || 0).toLocaleString()}
                        </td>
                      ))}
                    </tr>
                  ))}

                  {/* Totals row */}
                  <tr style={{ background:'var(--panel-2)', fontWeight:600 }}>
                    <td><span className="strong">Total</span></td>
                    <td className="mono strong" style={{ textAlign:'right' }}>
                      {agents.reduce((a, r) => a + r.total, 0).toLocaleString()}
                    </td>
                    {VISIBLE_STATUSES.map(s => {
                      const sum = agents.reduce((a, r) => a + (r.by_status?.[s] || 0), 0);
                      return <td key={s} className="mono" style={{ textAlign:'right' }}>{sum.toLocaleString()}</td>;
                    })}
                  </tr>
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>
    </>
  );
}
