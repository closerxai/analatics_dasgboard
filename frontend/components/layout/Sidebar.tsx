'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { logout, getMe, getMyCompany, getRBACScan } from '@/lib/api';
import { getInitials } from '@/lib/types';

interface NavItem {
  href: string;
  label: string;
  adminOnly?: boolean;
  badge?: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    href: '/',
    label: 'Dashboard',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <rect x="3" y="3" width="7" height="9" rx="1.5"/>
        <rect x="14" y="3" width="7" height="5" rx="1.5"/>
        <rect x="14" y="12" width="7" height="9" rx="1.5"/>
        <rect x="3" y="16" width="7" height="5" rx="1.5"/>
      </svg>
    ),
  },
  {
    href: '/source-wise',
    label: 'Source-wise',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M4 4h16v4H4z"/><path d="M4 10h16v4H4z"/><path d="M4 16h16v4H4z"/>
      </svg>
    ),
  },
  {
    href: '/leads-insights',
    label: 'Leads Insights',
    badge: 'leadsCount',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/>
        <path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/>
      </svg>
    ),
  },
  {
    href: '/sales-agents',
    label: 'Sales Agents',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M22 11l-3-3m0 0l-3 3m3-3v8"/>
      </svg>
    ),
  },
  {
    href: '/pipeline',
    label: 'Pipeline',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M4 6h6v6H4z"/><path d="M14 4h6v6h-6z"/>
        <path d="M14 14h6v6h-6z"/><path d="M4 16h6v4H4z"/>
      </svg>
    ),
  },
  {
    href: '/uploads',
    label: 'PR & Event Upload',
    adminOnly: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
    ),
  },
  {
    href: '/integrations',
    label: 'Integrations',
    adminOnly: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M8 7V3m8 4V3"/><path d="M3 11h18"/>
        <path d="M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"/>
      </svg>
    ),
  },
  {
    href: '/settings',
    label: 'Settings',
    adminOnly: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [user, setUser] = useState<{ username: string; email: string } | null>(null);
  const [company, setCompany] = useState<{ name: string } | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    getMe().then(setUser).catch(() => {});
    getMyCompany().then(setCompany).catch(() => {});
    getRBACScan().then(d => setIsAdmin(!!d.viewer?.is_admin)).catch(() => setIsAdmin(false));
  }, []);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="brand">
        <div className="brand-mark" />
        <div>
          <div className="brand-name">{company?.name || 'Emperium'}</div>
          <div className="brand-sub">CRM dashboard</div>
        </div>
      </div>

      {/* Views */}
      <div className="nav-group">Views</div>
      {NAV_ITEMS.slice(0, 5).map(item => (
        <Link
          key={item.href}
          href={item.href}
          className={`nav-item${isActive(item.href) ? ' active' : ''}`}
        >
          {item.icon}
          {item.label}
          {item.badge && (
            <span className="nav-badge mono">—</span>
          )}
        </Link>
      ))}

      {/* Workspace (admin only) */}
      {isAdmin && (
        <>
          <div className="nav-group">Workspace</div>
          {NAV_ITEMS.slice(5).map(item => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item${isActive(item.href) ? ' active' : ''}`}
            >
              {item.icon}
              {item.label}
            </Link>
          ))}
        </>
      )}

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="user-chip" onClick={logout} title="Click to logout">
          <div className="avatar">{user ? getInitials(user.username) : '—'}</div>
          <div style={{ lineHeight: 1.2 }}>
            <div style={{ fontWeight: 550, fontSize: '12.5px' }}>{user?.username || '…'}</div>
            <div className="muted" style={{ fontSize: '10.5px' }}>{user?.email || ''}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
