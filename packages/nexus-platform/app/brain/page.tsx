'use client';

import Sidebar from '@/components/Sidebar';
import { Brain, Database, Network, Lightbulb, Trash2, Download } from 'lucide-react';
import { useState, useEffect } from 'react';

interface MemoryItem {
  id: string;
  type: 'preference' | 'pattern' | 'bug' | 'wisdom';
  content: string;
  confidence: number;
  createdAt: string;
  accessCount: number;
}

const ZONES = [
  { key: 'preference', label: 'Preferences', icon: Lightbulb, color: 'var(--brand)' },
  { key: 'pattern', label: 'Patterns', icon: Network, color: 'var(--agent-architect)' },
  { key: 'bug', label: 'Bug History', icon: Database, color: 'var(--agent-debug)' },
  { key: 'wisdom', label: 'Wisdom', icon: Brain, color: 'var(--agent-parse)' },
];

export default function BrainPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [activeZone, setActiveZone] = useState('preference');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBrain = async () => {
      try {
        const res = await fetch('/api/brain');
        const data = await res.json();
        setMemories(data.memories || []);
      } catch {
        setMemories([]);
      }
      setLoading(false);
    };
    fetchBrain();
  }, []);

  const filtered = memories.filter(m => m.type === activeZone);

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">Brain</span>
            <span className="badge badge-brand" style={{ marginLeft: 8 }}>NEURON-X</span>
          </div>
          <div className="topbar-right">
            <button className="btn btn-ghost btn-sm"><Download size={14} /> Export</button>
            <button className="btn btn-ghost btn-sm" style={{ color: 'var(--danger)' }}><Trash2 size={14} /> Clear</button>
          </div>
        </div>

        <div className="page-content">
          {/* Stats */}
          <div className="stats-grid" style={{ marginBottom: 24 }}>
            <div className="stat-card">
              <div className="stat-label">Total Memories</div>
              <div className="stat-value brand">{memories.length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Preferences</div>
              <div className="stat-value">{memories.filter(m => m.type === 'preference').length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Patterns</div>
              <div className="stat-value">{memories.filter(m => m.type === 'pattern').length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Bug Fixes</div>
              <div className="stat-value">{memories.filter(m => m.type === 'bug').length}</div>
            </div>
          </div>

          {/* Zone Tabs */}
          <div className="tabs" style={{ marginBottom: 16 }}>
            {ZONES.map(z => (
              <button key={z.key} className={`tab ${activeZone === z.key ? 'active' : ''}`}
                onClick={() => setActiveZone(z.key)}>
                <z.icon size={14} style={{ marginRight: 6 }} /> {z.label}
              </button>
            ))}
          </div>

          {/* Memory List */}
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[1, 2, 3].map(i => (
                <div key={i} className="skeleton" style={{ height: 60, borderRadius: 'var(--radius-md)' }} />
              ))}
            </div>
          ) : filtered.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filtered.map(mem => (
                <div className="card" key={mem.id} style={{ padding: '14px 18px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>{mem.content}</div>
                      <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                        <span className="badge badge-gray">Confidence: {Math.round(mem.confidence * 100)}%</span>
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                          Accessed {mem.accessCount} times
                        </span>
                      </div>
                    </div>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{mem.createdAt}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state" style={{ minHeight: 300 }}>
              <div className="empty-state-icon"><Brain size={24} /></div>
              <div className="empty-state-title">No memories in this zone</div>
              <div className="empty-state-text">As you build projects, NEXUS-Ω will store patterns, preferences, and learnings here.</div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
