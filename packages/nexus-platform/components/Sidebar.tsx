'use client';

import { useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Home, Wand2, FolderOpen, Brain, Bug, Rocket, Settings, Zap } from 'lucide-react';

const NAV = [
  { href: '/dashboard', icon: Home, label: 'Dashboard' },
  { href: '/build', icon: Wand2, label: 'Build' },
  { href: '/projects', icon: FolderOpen, label: 'Projects' },
  { href: '/brain', icon: Brain, label: 'Brain' },
  { href: '/debug', icon: Bug, label: 'Debug' },
  { href: '/deploy', icon: Rocket, label: 'Deploy' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand" onClick={() => router.push('/dashboard')} style={{ cursor: 'pointer' }}>
        <div className="sidebar-brand-icon">
          <Zap size={16} />
        </div>
        <span className="sidebar-brand-text">NEXUS-Ω</span>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(item => (
          <button
            key={item.href}
            className={`sidebar-item ${pathname === item.href ? 'active' : ''}`}
            onClick={() => router.push(item.href)}
          >
            <item.icon size={18} className="icon" />
            <span>{item.label}</span>
          </button>
        ))}

        <div style={{ flex: 1 }} />

        <button
          className={`sidebar-item ${pathname === '/settings' ? 'active' : ''}`}
          onClick={() => router.push('/settings')}
        >
          <Settings size={18} className="icon" />
          <span>Settings</span>
        </button>
      </nav>

      <div className="sidebar-user">
        <div className="sidebar-avatar">K</div>
        <div>
          <div style={{ fontSize: '0.82rem', fontWeight: 600 }}>Karthik</div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Pro Plan</div>
        </div>
      </div>
    </aside>
  );
}
