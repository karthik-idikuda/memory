'use client';

import Sidebar from '@/components/Sidebar';
import { FolderOpen, Brain, Shield, Zap, Wand2, ArrowRight, Bug } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const router = useRouter();

  const agents = [
    { name: 'PARSE', color: 'var(--agent-parse)', status: 'Ready' },
    { name: 'ARCHITECT', color: 'var(--agent-architect)', status: 'Ready' },
    { name: 'CODEGEN', color: 'var(--agent-build)', status: 'Ready' },
    { name: 'SECURITY', color: 'var(--agent-security)', status: 'Ready' },
    { name: 'DEBUG', color: 'var(--agent-debug)', status: 'Ready' },
    { name: 'DEPLOY', color: 'var(--agent-deploy)', status: 'Ready' },
  ];

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">Dashboard</span>
          </div>
          <div className="topbar-right">
            <button className="btn btn-brand btn-sm" onClick={() => router.push('/build')}>
              <Wand2 size={14} /> New Project
            </button>
          </div>
        </div>

        <div className="page-content">
          {/* Stats Grid */}
          <div className="stats-grid" style={{ marginBottom: 20 }}>
            <div className="stat-card">
              <div className="stat-label">Total Projects</div>
              <div className="stat-value">0</div>
              <div className="stat-trend">Start building →</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Memories Stored</div>
              <div className="stat-value brand">0</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 4 }}>NEURON-X</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Avg Security Score</div>
              <div className="stat-value success">--</div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 4 }}>SECUREGEN-X</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Build Speed</div>
              <div className="stat-value" style={{ color: 'var(--agent-parse)' }}>800<span style={{ fontSize: '0.85rem', fontWeight: 400 }}> t/s</span></div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 4 }}>Groq LLM</div>
            </div>
          </div>

          {/* Agent Health */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 10 }}>Agent Status</h3>
            <div className="agents-grid">
              {agents.map(a => (
                <div className="agent-card" key={a.name}>
                  <div className="agent-name">
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: a.color }} />
                    {a.name}
                  </div>
                  <div className="agent-status">
                    <span className="pulse-dot" style={{ '--success': a.color } as React.CSSProperties} /> {a.status}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Start */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 10 }}>Quick Start</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              <div className="card" style={{ cursor: 'pointer', textAlign: 'center', padding: 28 }} onClick={() => router.push('/build')}>
                <Wand2 size={24} style={{ color: 'var(--brand)', marginBottom: 10 }} />
                <div className="feature-title">Start a new project</div>
                <div className="feature-desc">Describe what you want to build</div>
              </div>
              <div className="card" style={{ cursor: 'pointer', textAlign: 'center', padding: 28 }} onClick={() => router.push('/brain')}>
                <Brain size={24} style={{ color: 'var(--agent-architect)', marginBottom: 10 }} />
                <div className="feature-title">View your brain</div>
                <div className="feature-desc">See what NEXUS-Ω remembers</div>
              </div>
              <div className="card" style={{ cursor: 'pointer', textAlign: 'center', padding: 28 }} onClick={() => router.push('/debug')}>
                <Bug size={24} style={{ color: 'var(--agent-debug)', marginBottom: 10 }} />
                <div className="feature-title">Debug existing code</div>
                <div className="feature-desc">Paste code to find root causes</div>
              </div>
            </div>
          </div>

          {/* Recent Activity (empty state) */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Recent Activity</h3>
            </div>
            <div className="empty-state">
              <div className="empty-state-icon"><FolderOpen size={20} /></div>
              <div className="empty-state-title">No activity yet</div>
              <div className="empty-state-text">Start building something and your agent activity will appear here.</div>
              <button className="btn btn-brand btn-sm" style={{ marginTop: 16 }} onClick={() => router.push('/build')}>
                Start Building <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
