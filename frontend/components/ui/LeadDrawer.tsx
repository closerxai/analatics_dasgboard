'use client';

import { Lead, getInitials, LEAD_STATUS_LABELS } from '@/lib/types';
import { formatDistanceToNow } from 'date-fns';

interface Props {
  lead: Lead | null;
  onClose: () => void;
}

export default function LeadDrawer({ lead, onClose }: Props) {
  const open = !!lead;

  if (!open) return (
    <>
      <div className={`drawer-backdrop${open ? ' on' : ''}`} onClick={onClose} />
      <aside className={`drawer${open ? ' on' : ''}`} aria-hidden="true" />
    </>
  );

  const initials = getInitials(lead!.name);
  const statusKey = lead!.status;
  const ageDays = lead?.created_at
    ? Math.max(1, Math.round((Date.now() - new Date(lead.created_at).getTime()) / 86400000))
    : 1;

  const tl = [
    {
      kind: 'accent', time: `${ageDays}d ago`,
      title: `Lead captured · ${lead!.source_name || 'Unknown source'}`,
      desc: `Project: ${lead!.project_name || '—'} · City: ${lead!.city || '—'}`,
    },
    lead!.assigned_to_name && {
      kind: 'accent', time: `${Math.max(1, ageDays - 1)}d ago`,
      title: 'Assigned to agent',
      desc: `Assigned to ${lead!.assigned_to_name}`,
    },
    lead!.whatsapp_status && lead!.whatsapp_status !== '—' && {
      kind: 'accent', time: `${Math.max(1, ageDays - 2)}d ago`,
      title: 'WhatsApp touchpoint',
      desc: `${lead!.whatsapp_status} · Brochure shared`,
    },
    {
      kind: statusKey === 'disqualified' || statusKey === 'not_responding' ? 'bad'
        : statusKey === 'booked_site_visit' || statusKey === 'site_visit_done' ? 'good' : 'accent',
      time: 'Now',
      title: `Status: ${LEAD_STATUS_LABELS[statusKey] || statusKey}`,
      desc: `Next follow-up: ${lead!.follow_up_date || '—'} · Plan: ${lead!.planning_for_visit || '—'}`,
      detail: [['Source', lead!.source_name || '—'], ['GHL ID', lead!.ghl_opportunity_id || '—']],
    },
  ].filter(Boolean) as any[];

  return (
    <>
      <div className={`drawer-backdrop${open ? ' on' : ''}`} onClick={onClose} />
      <aside className={`drawer${open ? ' on' : ''}`} aria-hidden={!open}>
        {/* Header */}
        <div className="drawer-head">
          <div className="avatar lg">{initials}</div>
          <div>
            <div className="drawer-name">{lead!.name}</div>
            <div className="drawer-meta">
              <span className="mono">{lead!.phone || '—'}</span>
              <span>·</span>
              <span>{lead!.city || '—'}{lead!.project_name ? ` · ${lead!.project_name}` : ''}</span>
              <span className={`badge b-${statusKey}`}>
                <span className="dot" />
                {LEAD_STATUS_LABELS[statusKey] || statusKey}
              </span>
            </div>
          </div>
          <button className="btn icon drawer-close" onClick={onClose}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Stats */}
        <div className="drawer-stats">
          <div className="ds-cell">
            <div className="ds-label">Lead age</div>
            <div className="ds-val mono">{ageDays}d</div>
          </div>
          <div className="ds-cell">
            <div className="ds-label">Stage</div>
            <div className="ds-val" style={{ fontSize: 13, fontFamily: 'Inter' }}>
              {lead!.ghl_pipeline_stage_name || LEAD_STATUS_LABELS[statusKey] || statusKey}
            </div>
          </div>
          <div className="ds-cell">
            <div className="ds-label">Value</div>
            <div className="ds-val mono" style={{ fontSize: 13 }}>
              {lead!.monetary_value ? `₹${parseFloat(lead!.monetary_value).toLocaleString('en-IN')}` : '—'}
            </div>
          </div>
          <div className="ds-cell">
            <div className="ds-label">Agent</div>
            <div className="ds-val" style={{ fontSize: 12, fontFamily: 'Inter' }}>
              {lead!.assigned_to_name || '—'}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="drawer-tabs">
          <div className="dtab on">Timeline</div>
          <div className="dtab">Properties</div>
          <div className="dtab">Notes</div>
        </div>

        {/* Timeline */}
        <div className="drawer-body">
          <div className="tl">
            {tl.map((t, i) => (
              <div key={i} className={`tl-item ${t.kind || ''}`}>
                <div className="tl-dot" />
                <div className="tl-head">
                  <span className="tl-title">{t.title}</span>
                  <span className="tl-time">{t.time}</span>
                </div>
                <div className="tl-desc">{t.desc}</div>
                {t.detail && (
                  <div className="tl-detail">
                    {t.detail.map(([k, v]: [string, string]) => (
                      <>
                        <span className="muted">{k}</span>
                        <b>{v}</b>
                      </>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Additional Properties */}
          <div style={{ marginTop: 24, borderTop: '1px solid var(--line)', paddingTop: 16 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 16px', fontSize: 12 }}>
              {[
                ['Email', lead!.email],
                ['Phone', lead!.phone],
                ['Source', lead!.source_name],
                ['City', lead!.city],
                ['Status', LEAD_STATUS_LABELS[statusKey]],
                ['GHL Stage', lead!.ghl_pipeline_stage_name],
                ['WhatsApp', lead!.whatsapp_status],
                ['Planning visit', lead!.planning_for_visit],
                ['Remarks', lead!.remarks],
              ].filter(([, v]) => v).map(([k, v]) => (
                <div key={String(k)}>
                  <div className="hint" style={{ marginBottom: 2 }}>{k}</div>
                  <div style={{ fontWeight: 500 }}>{String(v)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
