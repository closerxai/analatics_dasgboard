'use client';

import { useEffect, useState, useCallback } from 'react';
import Topbar from '@/components/layout/Topbar';
import LeadDrawer from '@/components/ui/LeadDrawer';
import { getLeads, getProjects } from '@/lib/api';
import { Lead, LEAD_STATUS_LABELS, LeadStatus, ALL_STATUSES, getSourceColor, getInitials } from '@/lib/types';

export default function LeadsInsightsPage() {
  const [projects, setProjects] = useState<{ id: number; name: string }[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(false);

  const [filters, setFilters] = useState({
    project: 'all',
    q: '',
    source: 'All',
    agent: 'All',
    city: 'All',
    status: 'Any',
  });

  const [agents, setAgents] = useState<string[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filters.project !== 'all') params.project = filters.project;
      if (filters.q) params.q = filters.q;
      if (filters.source !== 'All') params.source = filters.source;
      if (filters.agent !== 'All') params.agent = filters.agent;
      if (filters.city !== 'All') params.city = filters.city;
      if (filters.status !== 'Any') params.status = filters.status;
      const data = await getLeads(params);
      setLeads(data);
      setTotal(data.length);

      // Build filter option lists from returned data
      setSources(Array.from(new Set(data.map((l: Lead) => l.source_name).filter((v): v is string => !!v))).sort());
      setAgents(Array.from(new Set(data.map((l: Lead) => l.assigned_to_name).filter((v): v is string => !!v))).sort());
      setCities(Array.from(new Set(data.map((l: Lead) => l.city).filter((v): v is string => !!v))).sort());
    } catch {}
    setLoading(false);
  }, [filters]);

  useEffect(() => { getProjects().then(setProjects).catch(() => {}); }, []);

  useEffect(() => { fetchLeads(); }, [filters.project]); // auto-apply on project change

  function set(k: keyof typeof filters, v: string) {
    setFilters(prev => ({ ...prev, [k]: v }));
  }

  return (
    <>
      <Topbar crumb="Leads Insights">
        <select className="mini-select" value={filters.project} onChange={e => set('project', e.target.value)}>
          <option value="all">All Projects</option>
          {projects.map(p => <option key={p.id} value={String(p.id)}>{p.name}</option>)}
        </select>
        <button className="btn" onClick={() => setFilters(f => ({ ...f, q:'', source:'All', agent:'All', city:'All', status:'Any' }))}>
          Clear filters
        </button>
        <button className="btn primary">Export</button>
      </Topbar>

      <div className="page">
        <div className="page-head">
          <div>
            <h1 className="page-title">Leads Insights</h1>
            <div className="page-sub">Lead-level table · click a row to view journey</div>
          </div>
        </div>

        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Leads Table</div>
              <div className="card-sub">
                <span className="mono strong">{total.toLocaleString()}</span> leads shown
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="card-body tight" style={{ borderBottom:'1px solid var(--line)' }}>
            <div className="filter-panel">
              <div className="f-group" style={{ flex:'2 1 240px' }}>
                <span className="f-label">Search</span>
                <input
                  className="mini-input" style={{ width:'100%' }}
                  value={filters.q}
                  onChange={e => set('q', e.target.value)}
                  placeholder="Name, email, phone, remarks…"
                />
              </div>
              <div className="f-group" style={{ flex:'1 1 120px' }}>
                <span className="f-label">Source</span>
                <select className="mini-select" value={filters.source} onChange={e => set('source', e.target.value)}>
                  <option>All</option>
                  {sources.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div className="f-group" style={{ flex:'1 1 120px' }}>
                <span className="f-label">Agent</span>
                <select className="mini-select" value={filters.agent} onChange={e => set('agent', e.target.value)}>
                  <option>All</option>
                  {agents.map(a => <option key={a}>{a}</option>)}
                </select>
              </div>
              <div className="f-group" style={{ flex:'1 1 120px' }}>
                <span className="f-label">City</span>
                <select className="mini-select" value={filters.city} onChange={e => set('city', e.target.value)}>
                  <option>All</option>
                  {cities.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div className="f-group" style={{ flex:'1 1 160px' }}>
                <span className="f-label">Status</span>
                <select className="mini-select" value={filters.status} onChange={e => set('status', e.target.value)}>
                  <option>Any</option>
                  {ALL_STATUSES.map(s => (
                    <option key={s} value={s}>{LEAD_STATUS_LABELS[s]}</option>
                  ))}
                </select>
              </div>
              <div className="f-actions">
                <button className="btn" onClick={() => setFilters(f => ({ ...f, q:'', source:'All', agent:'All', city:'All', status:'Any' }))}>
                  Reset
                </button>
                <button className="btn primary" onClick={fetchLeads}>Apply</button>
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="table-wrap" style={{ maxHeight:580 }}>
            {loading ? (
              <div style={{ padding:40, textAlign:'center' }}><span className="spinner" /></div>
            ) : leads.length === 0 ? (
              <div className="empty-state">
                <h3>No leads match your filters</h3>
                <p>Try adjusting filters or sync more data from GHL</p>
              </div>
            ) : (
              <table className="data">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Project</th>
                    <th>Source</th>
                    <th>Assigned To</th>
                    <th>City</th>
                    <th>GHL Stage</th>
                    <th>Planning Visit</th>
                    <th>WhatsApp</th>
                    <th>Status</th>
                    <th>Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map(lead => (
                    <tr key={lead.id} onClick={() => setSelectedLead(lead)}>
                      <td>
                        <div style={{ fontWeight:650 }}>{lead.name}</div>
                      </td>
                      <td className="muted">{lead.email || '—'}</td>
                      <td className="mono">{lead.phone || '—'}</td>
                      <td>{lead.project_name || '—'}</td>
                      <td>
                        <span className="source-tag">
                          <span className="dot" style={{ background: getSourceColor(lead.source_name) }} />
                          {lead.source_name || '—'}
                        </span>
                      </td>
                      <td>{lead.assigned_to_name || '—'}</td>
                      <td>{lead.city || '—'}</td>
                      <td>
                        {lead.ghl_pipeline_stage_name ? (
                          <span className="kv">{lead.ghl_pipeline_stage_name}</span>
                        ) : '—'}
                      </td>
                      <td className="muted">{lead.planning_for_visit || '—'}</td>
                      <td>
                        {lead.whatsapp_status && lead.whatsapp_status !== '—' ? (
                          <span className="badge b-whatsapp"><span className="dot" />{lead.whatsapp_status}</span>
                        ) : <span className="muted">—</span>}
                      </td>
                      <td>
                        <span className={`badge b-${lead.status}`}>
                          <span className="dot" />
                          {LEAD_STATUS_LABELS[lead.status] || lead.status}
                        </span>
                      </td>
                      <td className="muted" style={{ maxWidth:200, overflow:'hidden', textOverflow:'ellipsis' }}>
                        {lead.remarks || '—'}
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
