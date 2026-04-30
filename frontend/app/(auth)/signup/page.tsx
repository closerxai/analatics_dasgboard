'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { signup, login } from '@/lib/api';

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: '', email: '', password: '', companyName: '', agniKey: '' });
  const [step, setStep] = useState<'account' | 'company'>('account');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function set(k: keyof typeof form, v: string) {
    setForm(f => ({ ...f, [k]: v }));
  }

  async function handleAccountSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signup(form.username, form.email, form.password);
      await login(form.username, form.password);
      setStep('company');
    } catch (err: any) {
      setError(err.message || 'Sign-up failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleCompanySubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { createCompany } = await import('@/lib/api');
      await createCompany({ name: form.companyName, agni_api_key: form.agniKey || 'default' });
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Failed to create company');
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
        width: 380, background: 'var(--panel)',
        border: '1px solid var(--line)', borderRadius: 16,
        padding: 32, boxShadow: 'var(--shadow)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 28 }}>
          <div className="brand-mark" />
          <div>
            <div className="brand-name">Emperium</div>
            <div className="brand-sub">CRM dashboard</div>
          </div>
        </div>

        {step === 'account' ? (
          <>
            <h1 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 4px' }}>Create account</h1>
            <p className="muted" style={{ fontSize: 12.5, marginBottom: 24 }}>Step 1 of 2 — Account details</p>

            {error && (
              <div style={{ background: 'var(--bad-bg)', color: 'var(--bad)', border: '1px solid oklch(82% 0.05 25)', borderRadius: 8, padding: '8px 12px', fontSize: 12.5, marginBottom: 16 }}>
                {error}
              </div>
            )}

            <form onSubmit={handleAccountSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="form-group">
                <label className="form-label">Username</label>
                <input className="form-input" value={form.username} onChange={e => set('username', e.target.value)} required placeholder="john_doe" autoFocus />
              </div>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input className="form-input" type="email" value={form.email} onChange={e => set('email', e.target.value)} required placeholder="john@company.com" />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input className="form-input" type="password" value={form.password} onChange={e => set('password', e.target.value)} required placeholder="••••••••" minLength={8} />
              </div>
              <button type="submit" className="btn primary" disabled={loading} style={{ width: '100%', justifyContent: 'center', height: 38, marginTop: 4 }}>
                {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Continue'}
              </button>
            </form>
          </>
        ) : (
          <>
            <h1 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 4px' }}>Create workspace</h1>
            <p className="muted" style={{ fontSize: 12.5, marginBottom: 24 }}>Step 2 of 2 — Company details</p>

            {error && (
              <div style={{ background: 'var(--bad-bg)', color: 'var(--bad)', border: '1px solid oklch(82% 0.05 25)', borderRadius: 8, padding: '8px 12px', fontSize: 12.5, marginBottom: 16 }}>
                {error}
              </div>
            )}

            <form onSubmit={handleCompanySubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="form-group">
                <label className="form-label">Company name</label>
                <input className="form-input" value={form.companyName} onChange={e => set('companyName', e.target.value)} required placeholder="Acme Real Estate" autoFocus />
              </div>
              <div className="form-group">
                <label className="form-label">API key (optional)</label>
                <input className="form-input" value={form.agniKey} onChange={e => set('agniKey', e.target.value)} placeholder="sk-…" />
              </div>
              <button type="submit" className="btn primary" disabled={loading} style={{ width: '100%', justifyContent: 'center', height: 38, marginTop: 4 }}>
                {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Create workspace'}
              </button>
            </form>
          </>
        )}

        <p className="muted" style={{ marginTop: 20, fontSize: 12, textAlign: 'center' }}>
          Already have an account?{' '}
          <Link href="/login" style={{ color: 'var(--accent)', textDecoration: 'none' }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
