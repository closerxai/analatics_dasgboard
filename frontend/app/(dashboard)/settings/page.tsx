'use client';

import { useEffect, useMemo, useState } from 'react';
import Topbar from '@/components/layout/Topbar';
import {
  getMyCompany,
  updateMyCompany,
  getRBACScan,
  listPermissions,
  createRole,
  updateRole,
  listInvitations,
  createInvitation,
  listJoinRequests,
  approveJoinRequest,
  rejectJoinRequest,
} from '@/lib/api';

type Perm = { id: number; code: string; description: string };
type Role = { id: number; name: string; is_default: boolean; permissions: Perm[] };
type Invite = { id: number; email: string; role: number | null; role_name?: string | null; token: string; is_accepted: boolean; created_at: string };
type JoinReq = { id: number; status: string; message?: string; created_at: string; username?: string; email?: string };

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [company, setCompany] = useState<{ id: number; name: string; agni_api_key?: string; is_active?: boolean } | null>(null);
  const [companyDraft, setCompanyDraft] = useState<{ name: string; agni_api_key: string; is_active: boolean } | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [perms, setPerms] = useState<Perm[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [joinRequests, setJoinRequests] = useState<JoinReq[]>([]);

  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null);
  const selectedRole = useMemo(() => roles.find(r => r.id === selectedRoleId) || null, [roles, selectedRoleId]);

  const [roleForm, setRoleForm] = useState<{ name: string; is_default: boolean; permission_ids: number[] }>({ name: '', is_default: false, permission_ids: [] });
  const [inviteForm, setInviteForm] = useState<{ email: string; role_id: number | null }>({ email: '', role_id: null });
  const [createdToken, setCreatedToken] = useState<string>('');

  async function refreshAll() {
    setLoading(true);
    setError('');
    try {
      const [c, scan] = await Promise.all([getMyCompany() as any, getRBACScan()]);
      if (!scan?.viewer?.is_admin) {
        setCompany(c);
        setError('Access denied: only company admins can view Settings.');
        setRoles([]);
        setPerms([]);
        setInvites([]);
        return;
      }

      const [p, inv] = await Promise.all([listPermissions(), listInvitations()]);
      const jr = await listJoinRequests();
      setCompany(c);
      setCompanyDraft({
        name: c?.name || '',
        agni_api_key: c?.agni_api_key || '',
        is_active: c?.is_active ?? true,
      });
      setRoles((scan.roles || []) as Role[]);
      setPerms(p as Perm[]);
      setInvites(inv as Invite[]);
      setJoinRequests(jr as JoinReq[]);

      const first = (scan.roles || [])[0];
      if (first?.id) setSelectedRoleId(first.id);
    } catch (e: any) {
      setError(e?.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedRole) return;
    setRoleForm({
      name: selectedRole.name,
      is_default: selectedRole.is_default,
      permission_ids: selectedRole.permissions?.map(p => p.id) || [],
    });
  }, [selectedRole]);

  async function saveCompany() {
    if (!companyDraft) return;
    setError('');
    try {
      const updated = await updateMyCompany(companyDraft);
      setCompany(updated as any);
    } catch (e: any) {
      setError(e?.message || 'Failed to update company');
    }
  }

  async function saveRole() {
    if (!selectedRoleId) return;
    setError('');
    try {
      await updateRole(selectedRoleId, roleForm);
      await refreshAll();
    } catch (e: any) {
      setError(e?.message || 'Failed to update role');
    }
  }

  async function createNewRole() {
    setError('');
    try {
      const r: any = await createRole({ name: roleForm.name || 'New Role', is_default: roleForm.is_default, permission_ids: roleForm.permission_ids });
      setSelectedRoleId(r.id);
      await refreshAll();
    } catch (e: any) {
      setError(e?.message || 'Failed to create role');
    }
  }

  async function createInvite() {
    setError('');
    setCreatedToken('');
    try {
      const inv: any = await createInvitation({ email: inviteForm.email, role_id: inviteForm.role_id });
      setCreatedToken(inv.token);
      setInviteForm({ email: '', role_id: null });
      await refreshAll();
    } catch (e: any) {
      setError(e?.message || 'Failed to create invitation');
    }
  }

  async function approveJR(id: number, roleId: number | null) {
    setError('');
    try {
      await approveJoinRequest(id, roleId);
      await refreshAll();
    } catch (e: any) {
      setError(e?.message || 'Failed to approve join request');
    }
  }

  async function rejectJR(id: number) {
    setError('');
    try {
      await rejectJoinRequest(id);
      await refreshAll();
    } catch (e: any) {
      setError(e?.message || 'Failed to reject join request');
    }
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {}
  }

  if (loading) {
    return (
      <>
        <Topbar crumb="Settings" />
        <div className="page">
          <section className="card">
            <div className="card-body">
              <div className="muted">Loading…</div>
            </div>
          </section>
        </div>
      </>
    );
  }

  return (
    <>
      <Topbar crumb="Settings" />

      <div className="page">
        {error && (
          <section className="card" style={{ borderColor: 'oklch(82% 0.05 25)' }}>
            <div className="card-body" style={{ color: 'var(--bad)' }}>
              {error}
            </div>
          </section>
        )}

        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Company</div>
              <div className="card-sub">Edit workspace details</div>
            </div>
          </div>
          <div className="card-body" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 160px', gap: 12 }}>
            <div className="form-group">
              <label className="form-label">Company name</label>
              <input className="form-input" value={companyDraft?.name || ''} onChange={e => setCompanyDraft(d => d ? ({ ...d, name: e.target.value }) : d)} />
            </div>
            <div className="form-group">
              <label className="form-label">AGNI API key</label>
              <input className="form-input" value={companyDraft?.agni_api_key || ''} onChange={e => setCompanyDraft(d => d ? ({ ...d, agni_api_key: e.target.value }) : d)} placeholder="sk-…" />
            </div>
            <div className="form-group">
              <label className="form-label">Active</label>
              <button className="btn" onClick={() => setCompanyDraft(d => d ? ({ ...d, is_active: !d.is_active }) : d)}>
                {companyDraft?.is_active ? 'Enabled' : 'Disabled'}
              </button>
            </div>
            <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 8 }}>
              <button className="btn primary" onClick={saveCompany}>Save company</button>
              <span className="hint mono">id: {company?.id}</span>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Roles & Permissions</div>
              <div className="card-sub">Create roles and assign permissions</div>
            </div>
          </div>
          <div className="card-body" style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 12 }}>
            <div style={{ border: '1px solid var(--line)', borderRadius: 10, overflow: 'hidden' }}>
              <div style={{ padding: 10, borderBottom: '1px solid var(--line)', background: 'var(--panel-2)', fontWeight: 600 }}>
                Roles
              </div>
              <div style={{ padding: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {roles.map(r => (
                  <button
                    key={r.id}
                    className={`btn${selectedRoleId === r.id ? ' primary' : ''}`}
                    style={{ justifyContent: 'space-between' }}
                    onClick={() => setSelectedRoleId(r.id)}
                  >
                    <span>{r.name}</span>
                    <span className="hint mono">{r.is_default ? 'default' : ''}</span>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ border: '1px solid var(--line)', borderRadius: 10, padding: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div style={{ fontWeight: 650 }}>Edit role</div>
                <div className="hint mono">selected: {selectedRoleId ?? '—'}</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 160px', gap: 12, alignItems: 'end' }}>
                <div className="form-group">
                  <label className="form-label">Role name</label>
                  <input className="form-input" value={roleForm.name} onChange={e => setRoleForm(f => ({ ...f, name: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Default</label>
                  <button className="btn" onClick={() => setRoleForm(f => ({ ...f, is_default: !f.is_default }))}>
                    {roleForm.is_default ? 'Yes' : 'No'}
                  </button>
                </div>
              </div>

              <div style={{ marginTop: 10, borderTop: '1px solid var(--line)', paddingTop: 10 }}>
                <div className="muted" style={{ marginBottom: 8 }}>Permissions</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {perms.map(p => {
                    const on = roleForm.permission_ids.includes(p.id);
                    return (
                      <label key={p.id} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', padding: 8, border: '1px solid var(--line)', borderRadius: 10, background: on ? 'var(--accent-bg)' : 'transparent' }}>
                        <input
                          type="checkbox"
                          checked={on}
                          onChange={() => setRoleForm(f => ({
                            ...f,
                            permission_ids: on ? f.permission_ids.filter(x => x !== p.id) : [...f.permission_ids, p.id],
                          }))}
                          style={{ marginTop: 2 }}
                        />
                        <div>
                          <div className="mono" style={{ fontSize: 11.5 }}>{p.code}</div>
                          <div className="muted" style={{ fontSize: 11 }}>{p.description}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button className="btn" onClick={createNewRole}>Create new role</button>
                <button className="btn primary" disabled={!selectedRoleId} onClick={saveRole}>Save role</button>
              </div>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Invitations</div>
              <div className="card-sub">Invite members to join your company</div>
            </div>
          </div>
          <div className="card-body" style={{ display: 'grid', gridTemplateColumns: '1fr 220px 160px', gap: 12, alignItems: 'end' }}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" value={inviteForm.email} onChange={e => setInviteForm(f => ({ ...f, email: e.target.value }))} placeholder="user@company.com" />
            </div>
            <div className="form-group">
              <label className="form-label">Role</label>
              <select className="form-input" value={inviteForm.role_id ?? ''} onChange={e => setInviteForm(f => ({ ...f, role_id: e.target.value ? Number(e.target.value) : null }))}>
                <option value="">(default)</option>
                {roles.map(r => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </div>
            <button className="btn primary" onClick={createInvite} disabled={!inviteForm.email}>Create invite</button>

            {createdToken && (
              <div style={{ gridColumn: '1 / -1', borderTop: '1px solid var(--line)', paddingTop: 10 }}>
                <div className="muted" style={{ marginBottom: 6 }}>Invitation token (share with the invited user)</div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <code style={{ padding: '8px 10px', borderRadius: 10, border: '1px solid var(--line)', background: 'var(--panel-2)', flex: 1, overflowX: 'auto' }}>
                    {createdToken}
                  </code>
                  <button className="btn" onClick={() => copy(createdToken)}>Copy</button>
                </div>
              </div>
            )}

            <div style={{ gridColumn: '1 / -1', borderTop: '1px solid var(--line)', paddingTop: 10 }}>
              <div className="muted" style={{ marginBottom: 8 }}>Recent invitations</div>
              {invites.length === 0 ? (
                <div className="muted">No invitations yet.</div>
              ) : (
                <table className="data">
                  <thead>
                    <tr>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th className="mono">Token</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {invites.map(i => (
                      <tr key={i.id}>
                        <td>{i.email}</td>
                        <td>{i.role_name || 'Default'}</td>
                        <td>{i.is_accepted ? 'Accepted' : 'Pending'}</td>
                        <td className="mono" style={{ maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis' }}>{i.token}</td>
                        <td style={{ textAlign: 'right' }}>
                          <button className="btn" onClick={() => copy(i.token)}>Copy</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-head">
            <div>
              <div className="card-title">Join Requests</div>
              <div className="card-sub">Approve/reject requests and assign roles</div>
            </div>
          </div>
          <div className="card-body">
            {joinRequests.length === 0 ? (
              <div className="muted">No join requests.</div>
            ) : (
              <table className="data">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Message</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {joinRequests.map(j => (
                    <JoinRequestRow key={j.id} jr={j} roles={roles} onApprove={approveJR} onReject={rejectJR} />
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>
    </>
  );
}

function JoinRequestRow({
  jr,
  roles,
  onApprove,
  onReject,
}: {
  jr: JoinReq;
  roles: Role[];
  onApprove: (id: number, roleId: number | null) => void;
  onReject: (id: number) => void;
}) {
  const [roleId, setRoleId] = useState<number | null>(roles.find(r => r.is_default)?.id ?? (roles[0]?.id ?? null));
  const processed = jr.status !== 'pending';

  return (
    <tr>
      <td>
        <div style={{ display: 'grid' }}>
          <span>{jr.username || '—'}</span>
          <span className="muted" style={{ fontSize: 11 }}>{jr.email || ''}</span>
        </div>
      </td>
      <td className="muted">{jr.message || '—'}</td>
      <td>
        <select className="form-input" value={roleId ?? ''} onChange={e => setRoleId(e.target.value ? Number(e.target.value) : null)} disabled={processed}>
          <option value="">(default)</option>
          {roles.map(r => (
            <option key={r.id} value={r.id}>{r.name}</option>
          ))}
        </select>
      </td>
      <td>{jr.status}</td>
      <td style={{ textAlign: 'right' }}>
        {!processed ? (
          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
            <button className="btn" onClick={() => onReject(jr.id)}>Reject</button>
            <button className="btn primary" onClick={() => onApprove(jr.id, roleId)}>Approve</button>
          </div>
        ) : (
          <span className="muted">—</span>
        )}
      </td>
    </tr>
  );
}
