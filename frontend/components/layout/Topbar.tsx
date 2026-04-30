'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface TopbarProps {
  crumb?: string;
  children?: React.ReactNode;
}

export default function Topbar({ crumb, children }: TopbarProps) {
  const [dark, setDark] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    // Read saved theme
    const saved = localStorage.getItem('theme');
    const isDark = saved !== null ? saved === 'dark' : true;
    setDark(isDark);
    document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
  }, []);

  useEffect(() => {
    const interval = setInterval(() => setTick(t => (t + 1) % 60), 1000);
    return () => clearInterval(interval);
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? 'dark' : 'light';
    localStorage.setItem('theme', next ? 'dark' : 'light');
  }

  return (
    <div className="topbar">
      <div className="crumbs">
        <span>Workspace</span>
        <span>›</span>
        <b>{crumb || 'Dashboard'}</b>
      </div>

      <div className="search">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>
        </svg>
        <input placeholder="Search contacts, deals, campaigns…" />
        <kbd>⌘K</kbd>
      </div>

      {/* Live ticker */}
      <span className="hint mono" style={{ marginLeft: 4 }}>updated {tick}s ago</span>

      {/* Theme toggle */}
      <button className="btn icon" onClick={toggleTheme} title="Toggle theme">
        {dark ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
          </svg>
        )}
      </button>

      {/* Notification bell */}
      <button className="btn icon" title="Notifications">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.7 21a2 2 0 0 1-3.4 0"/>
        </svg>
      </button>

      {/* Custom slot for page-specific actions */}
      {children}

      <Link href="/leads-insights">
        <button className="btn primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          New Lead
        </button>
      </Link>
    </div>
  );
}
