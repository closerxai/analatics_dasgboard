'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { acceptInvitation } from '@/lib/api';

export default function AcceptInvitePage() {
  const router = useRouter();
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await acceptInvitation(token.trim());
      router.push('/');
    } catch (err: any) {
      setError(err?.message || 'Failed to accept invitation');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: 'var(--bg)',
    }}>
      <div style={{
        width: 420, background: 'var(--panel)',
        border: '1px solid var(--line)', borderRadius: 16,
        padding: 32, boxShadow: 'var(--shadow)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
          <div className="brand-mark" />
          <div>
            <div className="brand-name">Emperium</div>
            <div className="brand-sub">Join workspace</div>
          </div>
        </div>

        <h1 style={{ fontSize: 18, fontWeight: 650, margin: '0 0 6px' }}>Accept invitation</h1>
        <p className="muted" style={{ fontSize: 12.5, marginBottom: 18 }}>
          Paste the invitation token you received from your admin.
        </p>

        {error && (
          <div style={{ background: 'var(--bad-bg)', color: 'var(--bad)', border: '1px solid oklch(82% 0.05 25)', borderRadius: 8, padding: '8px 12px', fontSize: 12.5, marginBottom: 16 }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="form-group">
            <label className="form-label">Invitation token</label>
            <input className="form-input" value={token} onChange={e => setToken(e.target.value)} required placeholder="paste token…" autoFocus />
          </div>
          <button type="submit" className="btn primary" disabled={loading} style={{ width: '100%', justifyContent: 'center', height: 38 }}>
            {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Join workspace'}
          </button>
        </form>

        <p className="muted" style={{ marginTop: 16, fontSize: 12, textAlign: 'center' }}>
          Back to{' '}
          <Link href="/" style={{ color: 'var(--accent)', textDecoration: 'none' }}>Dashboard</Link>
        </p>
      </div>
    </div>
  );
}

