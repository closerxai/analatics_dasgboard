'use client';

import { useEffect, useState } from 'react';
import Topbar from '@/components/layout/Topbar';
import DonutChart from '@/components/charts/DonutChart';
import Heatmap from '@/components/charts/Heatmap';
import LeadFlowSvg from '@/components/charts/LeadFlowSvg';
import LeadDrawer from '@/components/ui/LeadDrawer';
import { getKPIs, getSources, getLeads } from '@/lib/api';
import { Lead, KPI, getInitials, getSourceColor, LEAD_STATUS_LABELS, formatCurrency } from '@/lib/types';

const ICONS: Record<string, string> = {
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  pin:   '<path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 1 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
  trophy:'<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4zM17 4h3a2 2 0 0 1 0 4h-3M7 4H4a2 2 0 0 0 0 4h3"/>',
  funnel:'<path d="M3 4h18l-7 9v6l-4 2v-8L3 4z"/>',
  phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
};

const STATIC_KPIS: KPI[] = [
  { label:'Total Leads',        val:'—', delta:'—', up:true,  accent:'primary', icon:'users' },
  { label:'Qualified',          val:'—', delta:'—', up:true,  accent:'primary', icon:'check' },
  { label:'Site Visits Booked', val:'—', delta:'—', up:true,  accent:'good',    icon:'pin' },
  { label:'Deals Closed',       val:'—', delta:'—', up:true,  accent:'good',    icon:'trophy' },
  { label:'Conversion',         val:'—', delta:'—', up:true,  accent:'primary', icon:'funnel' },
];

const CALL_BARS = [
  { label:'Answered',          n:3008, pct:62.4, color:'var(--good)' },
  { label:'Not answered',      n:1102, pct:22.9, color:'var(--ink-3)' },
  { label:'Busy / Voicemail',  n:478,  pct:9.9,  color:'var(--warn)' },
  { label:'Wrong number',      n:233,  pct:4.8,  color:'var(--bad)' },
];

const OUTCOMES = [
  { label:'Interested',     n:1204, pct:40.0, color:'var(--good)' },
  { label:'Callback',       n:812,  pct:27.0, color:'var(--accent)' },
  { label:'Not interested', n:602,  pct:20.0, color:'var(--bad)' },
  { label:'No response',    n:390,  pct:13.0, color:'var(--ink-3)' },
];

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPI[]>(STATIC_KPIS);
  const [sources, setSources] = useState<{ name: string; n: number }[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    getKPIs(days).then(d => setKpis(d.kpis)).catch(() => {});
    getSources(days).then(d => {
      setSources(d.sources.map((s: any) => ({ name: s.name, n: s.total })));
    }).catch(() => {});
    getLeads({ limit: '20' }).then(data => setLeads(data)).catch(() => {});
  }, [days]);

  return (
    <>
      <Topbar crumb="Dashboard">
        <div className="seg" role="tablist">
          {[7, 30].map(d => (
            <button key={d} className={days === d ? 'on' : ''} onClick={() => setDays(d)}>
              {d}d
            </button>
          ))}
          <button>QTD</button>
          <button>YTD</button>
        </div>
      </Topbar>

      <div className="page">
        {/* Header */}
        <div className="page-head">
          <div>
            <h1 className="page-title">
              Lead Analytics{' '}
              <span className="live-pill">
                <span className="live-dot" />Live
              </span>
            </h1>
            <div className="page-sub">
              Conversion performance across all sources · last {days} days
            </div>
          </div>
          <button className="btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Export
          </button>
        </div>

        {/* KPI row */}
        <div className="kpi-row">
          {kpis.map(k => (
            <div key={k.label} className={`kpi accent-${k.accent}`}>
              <div className="label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
                  dangerouslySetInnerHTML={{ __html: ICONS[k.icon] || '' }} />
                {k.label}
              </div>
              <div className="val">{String(k.val)}</div>
              <div className={`delta ${k.up ? 'up' : 'down'}`}>
                <span>{k.up ? '↑' : '↓'}</span>
                <span className="mono">{k.delta}</span>
                <span className="muted" style={{ fontWeight: 400 }}>vs prev {days}d</span>
              </div>
            </div>
          ))}
        </div>

        {/* Lead Lifecycle Flow */}
        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Lead Lifecycle Flow</div>
              <div className="card-sub">Lead stages in motion · live counts overlaid on each node · click a node to filter</div>
            </div>
          </div>
          <div className="flow-scroll">
            <LeadFlowSvg />
          </div>
          <div className="flow-legend">
            <span className="lg"><span className="sw" style={{ background:'oklch(62% 0.14 150)' }} />Positive outcome</span>
            <span className="lg"><span className="sw" style={{ background:'oklch(62% 0.16 25)' }} />Drop / negative</span>
            <span className="lg"><span className="sw" style={{ background:'oklch(72% 0.14 75)' }} />Ops / scheduled</span>
            <span className="lg"><span className="sw" style={{ background:'oklch(55% 0.04 250)' }} />Neutral</span>
            <span style={{ marginLeft:'auto' }} className="hint mono">avg transit 3.8 calls · 5.2 days lead→site-visit</span>
          </div>
        </section>

        {/* Donut + Heatmap */}
        <div className="row-half">
          <section className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Lead Sources</div>
                <div className="card-sub">Attribution · last {days} days</div>
              </div>
            </div>
            <div className="card-body">
              <DonutChart data={sources.length ? sources : []} />
              {!sources.length && (
                <div className="empty-state">
                  <p>No source data yet — connect GHL and sync leads</p>
                </div>
              )}
            </div>
          </section>

          <section className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Best Performing Hours</div>
                <div className="card-sub">Answered-call rate by day × hour</div>
              </div>
              <span className="hint mono">avg 34%</span>
            </div>
            <div className="card-body">
              <Heatmap />
            </div>
          </section>
        </div>

        {/* Call bars + outcomes */}
        <div className="row-2">
          <section className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Call Analytics</div>
                <div className="card-sub">4,821 calls · avg 3.8 attempts per conversion</div>
              </div>
              <div style={{ display:'flex', gap:14, alignItems:'center' }}>
                <div style={{ textAlign:'right' }}>
                  <div className="hint">Answered rate</div>
                  <div className="mono strong" style={{ fontSize:15 }}>62.4%</div>
                </div>
                <div className="divider-v" />
                <div style={{ textAlign:'right' }}>
                  <div className="hint">Avg duration</div>
                  <div className="mono strong" style={{ fontSize:15 }}>2:41</div>
                </div>
              </div>
            </div>
            <div className="card-body">
              <div className="bar-stack">
                {CALL_BARS.map(b => (
                  <div key={b.label} className="bar-row">
                    <span>{b.label}</span>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width:`${b.pct}%`, background:b.color }} />
                    </div>
                    <span className="mono muted" style={{ textAlign:'right' }}>{b.n.toLocaleString()} · {b.pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="card">
            <div className="card-head">
              <div>
                <div className="card-title">Call Outcome Breakdown</div>
                <div className="card-sub">Dispositions on answered calls</div>
              </div>
              <span className="hint mono">3,008 answered</span>
            </div>
            <div className="card-body">
              <div className="bar-stack">
                {OUTCOMES.map(b => (
                  <div key={b.label} className="bar-row">
                    <span>{b.label}</span>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width:`${b.pct * 2}%`, background:b.color }} />
                    </div>
                    <span className="mono muted" style={{ textAlign:'right' }}>{b.n.toLocaleString()} · {b.pct}%</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>

        {/* Contacts table */}
        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Contacts</div>
              <div className="card-sub">
                <span>{leads.length}</span> contacts · click a row for deep-dive
              </div>
            </div>
            <div style={{ display:'flex', gap:6 }}>
              <button className="btn">Export CSV</button>
            </div>
          </div>

          <div className="table-wrap">
            {leads.length === 0 ? (
              <div className="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M22 11l-3-3m0 0l-3 3m3-3v8"/>
                </svg>
                <h3>No leads yet</h3>
                <p>Connect GHL in Integrations and run a sync</p>
              </div>
            ) : (
              <table className="data">
                <thead>
                  <tr>
                    <th>Contact</th>
                    <th>Source</th>
                    <th>Status</th>
                    <th>Agent</th>
                    <th>City</th>
                    <th style={{ textAlign:'right' }}>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map(lead => (
                    <tr key={lead.id} onClick={() => setSelectedLead(lead)}>
                      <td>
                        <div className="contact-cell">
                          <div className="avatar">{getInitials(lead.name)}</div>
                          <div>
                            <div className="contact-name">{lead.name}</div>
                            <div className="phone">{lead.phone || lead.email || '—'}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="source-tag">
                          <span className="dot" style={{ background: getSourceColor(lead.source_name) }} />
                          {lead.source_name || '—'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge b-${lead.status}`}>
                          <span className="dot" />
                          {LEAD_STATUS_LABELS[lead.status] || lead.status}
                        </span>
                      </td>
                      <td>{lead.assigned_to_name || '—'}</td>
                      <td>{lead.city || '—'}</td>
                      <td className="mono" style={{ textAlign:'right' }}>
                        {formatCurrency(lead.monetary_value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>

      <LeadDrawer lead={selectedLead} onClose={() => setSelectedLead(null)} />
    </>
  );
}
