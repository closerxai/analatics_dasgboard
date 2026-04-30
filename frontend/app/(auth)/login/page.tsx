'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Invalid credentials');
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
        width: 360, background: 'var(--panel)',
        border: '1px solid var(--line)', borderRadius: 16,
        padding: 32, boxShadow: 'var(--shadow)',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 28 }}>
          <div className="brand-mark" />
          <div>
            <div className="brand-name">Emperium</div>
            <div className="brand-sub">CRM dashboard</div>
          </div>
        </div>

        <h1 style={{ fontSize: 20, fontWeight: 600, letterSpacing: -0.02, margin: '0 0 4px' }}>Sign in</h1>
        <p className="muted" style={{ fontSize: 12.5, marginBottom: 24 }}>
          Enter your credentials to continue
        </p>

        {error && (
          <div style={{
            background: 'var(--bad-bg)', color: 'var(--bad)',
            border: '1px solid oklch(82% 0.05 25)',
            borderRadius: 8, padding: '8px 12px',
            fontSize: 12.5, marginBottom: 16,
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              className="form-input"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
              placeholder="your_username"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            className="btn primary"
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', height: 38, marginTop: 4 }}
          >
            {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Sign in'}
          </button>
        </form>

        <p className="muted" style={{ marginTop: 20, fontSize: 12, textAlign: 'center' }}>
          Don't have an account?{' '}
          <Link href="/signup" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
            Create one
          </Link>
        </p>

        <p className="muted" style={{ marginTop: 10, fontSize: 12, textAlign: 'center' }}>
          Have an invite token?{' '}
          <Link href="/accept-invite" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
            Accept invitation
          </Link>
        </p>
      </div>
    </div>
  );
}
