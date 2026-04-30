'use client';

import { useEffect, useState } from 'react';
import Topbar from '@/components/layout/Topbar';
import { connectGHL, getGHLStatus, getRBACScan, registerGHLWebhook, triggerAutoSync } from '@/lib/api';

export default function IntegrationsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState<any>({ connected: false });

  const [locationId, setLocationId] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [webhookBaseUrl, setWebhookBaseUrl] = useState('');

  async function refresh() {
    setError('');
    setLoading(true);
    try {
      const scan = await getRBACScan();
      if (!scan?.viewer?.is_admin) {
        setStatus({ connected: false });
        setError('Access denied: only company admins can manage integrations.');
        return;
      }
      const s = await getGHLStatus();
      setStatus(s);
      if (s?.location_id) setLocationId(String(s.location_id));
    } catch (e: any) {
      setError(e?.message || 'Failed to load integration status');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    try {
      await connectGHL({
        location_id: locationId.trim(),
        api_key: apiKey.trim() || undefined,
        access_token: accessToken.trim() || undefined,
      });
      await refresh();
    } catch (e: any) {
      setError(e?.message || 'Failed to connect GHL');
    }
  }

  async function handleRegisterWebhook() {
    setError('');
    try {
      await registerGHLWebhook(webhookBaseUrl.trim());
      await refresh();
    } catch (e: any) {
      setError(e?.message || 'Failed to register webhook');
    }
  }

  async function handleSync() {
    setError('');
    try {
      await triggerAutoSync();
    } catch (e: any) {
      setError(e?.message || 'Sync failed');
    }
  }

  return (
    <>
      <Topbar crumb="Integrations" />
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
              <div className="card-title">GoHighLevel (GHL)</div>
              <div className="card-sub">Connect and sync opportunities/leads</div>
            </div>
            <span className="hint mono">
              {loading ? 'loading…' : status?.connected ? 'connected' : 'not connected'}
            </span>
          </div>

          <div className="card-body" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div style={{ border: '1px solid var(--line)', borderRadius: 12, padding: 12 }}>
              <div style={{ fontWeight: 650, marginBottom: 8 }}>Status</div>
              <div className="muted" style={{ display: 'grid', gap: 6 }}>
                <div><span className="mono">connected</span>: {String(!!status?.connected)}</div>
                <div><span className="mono">location_id</span>: {status?.location_id || '—'}</div>
                <div><span className="mono">auth_type</span>: {status?.auth_type || '—'}</div>
                <div><span className="mono">webhook_registered</span>: {String(!!status?.webhook_registered)}</div>
              </div>
              <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                <button className="btn" onClick={refresh}>Refresh</button>
                <button className="btn primary" onClick={handleSync} disabled={!status?.connected}>Run sync</button>
              </div>
            </div>

            <form onSubmit={handleConnect} style={{ border: '1px solid var(--line)', borderRadius: 12, padding: 12 }}>
              <div style={{ fontWeight: 650, marginBottom: 8 }}>Connect</div>
              <div className="form-group">
                <label className="form-label">Location ID</label>
                <input className="form-input" value={locationId} onChange={e => setLocationId(e.target.value)} required placeholder="GHL location/sub-account id" />
              </div>
              <div className="form-group" style={{ marginTop: 10 }}>
                <label className="form-label">API Key (optional)</label>
                <input className="form-input" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="ghl_api_key…" />
              </div>
              <div className="form-group" style={{ marginTop: 10 }}>
                <label className="form-label">Access Token (optional)</label>
                <input className="form-input" value={accessToken} onChange={e => setAccessToken(e.target.value)} placeholder="oauth_access_token…" />
              </div>
              <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
                Provide either API key or access token (at least one).
              </div>
              <button className="btn primary" type="submit" style={{ marginTop: 12 }}>Save connection</button>
            </form>

            <div style={{ gridColumn: '1 / -1', borderTop: '1px solid var(--line)', paddingTop: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 160px', gap: 10, alignItems: 'end' }}>
                <div className="form-group">
                  <label className="form-label">Webhook base URL</label>
                  <input className="form-input" value={webhookBaseUrl} onChange={e => setWebhookBaseUrl(e.target.value)} placeholder="https://your-backend.example.com" />
                </div>
                <button className="btn" onClick={handleRegisterWebhook} disabled={!webhookBaseUrl || !status?.connected}>
                  Register webhook
                </button>
              </div>
              <div className="muted" style={{ fontSize: 12, marginTop: 8 }}>
                Use your backend public URL (it registers `POST /api/webhook/ghl/`).
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
