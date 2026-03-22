'use client';

import Sidebar from '@/components/Sidebar';
import { Settings, Key, User, Palette, Brain, Shield, Save, Eye, EyeOff, CheckCircle2 } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function SettingsPage() {
  const [groqKey, setGroqKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<'api' | 'profile' | 'appearance' | 'memory'>('api');

  useEffect(() => {
    const stored = localStorage.getItem('nexus-groq-key');
    if (stored) setGroqKey(stored);
  }, []);

  const saveSettings = () => {
    localStorage.setItem('nexus-groq-key', groqKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">Settings</span>
          </div>
          <div className="topbar-right">
            <button className="btn btn-brand btn-sm" onClick={saveSettings}>
              {saved ? <><CheckCircle2 size={14} /> Saved!</> : <><Save size={14} /> Save</>}
            </button>
          </div>
        </div>

        <div className="page-content" style={{ maxWidth: 700, margin: '0 auto' }}>
          {/* Tabs */}
          <div className="tabs" style={{ marginBottom: 24 }}>
            {[
              { key: 'api', icon: Key, label: 'API Keys' },
              { key: 'profile', icon: User, label: 'Profile' },
              { key: 'appearance', icon: Palette, label: 'Appearance' },
              { key: 'memory', icon: Brain, label: 'Memory' },
            ].map(t => (
              <button key={t.key} className={`tab ${activeTab === t.key ? 'active' : ''}`}
                onClick={() => setActiveTab(t.key as typeof activeTab)}>
                <t.icon size={14} style={{ marginRight: 6 }} /> {t.label}
              </button>
            ))}
          </div>

          {/* API Keys Tab */}
          {activeTab === 'api' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="card">
                <h3 className="card-title" style={{ marginBottom: 14 }}>Groq API Key</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 12 }}>
                  Required for code generation. Get your key at <a href="https://console.groq.com" target="_blank" rel="noopener">console.groq.com</a>
                </p>
                <div style={{ display: 'flex', gap: 8 }}>
                  <div style={{ flex: 1, position: 'relative' }}>
                    <input
                      className="input font-mono"
                      type={showKey ? 'text' : 'password'}
                      placeholder="gsk_..."
                      value={groqKey}
                      onChange={e => setGroqKey(e.target.value)}
                    />
                    <button
                      className="btn btn-ghost btn-icon"
                      style={{ position: 'absolute', right: 4, top: '50%', transform: 'translateY(-50%)' }}
                      onClick={() => setShowKey(!showKey)}>
                      {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8 }}>
                  <Shield size={12} style={{ color: 'var(--success)' }} />
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Stored locally in your browser. Never sent to our servers.
                  </span>
                </div>
              </div>

              <div className="card">
                <h3 className="card-title" style={{ marginBottom: 14 }}>Model Configuration</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div>
                    <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Primary Model</label>
                    <select className="input" style={{ cursor: 'pointer' }}>
                      <option>llama-3.3-70b-versatile</option>
                      <option>llama-3.1-8b-instant</option>
                      <option>mixtral-8x7b-32768</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Temperature</label>
                    <input className="input" type="number" defaultValue={0.7} min={0} max={2} step={0.1} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Max Tokens</label>
                    <input className="input" type="number" defaultValue={4096} min={256} max={8192} step={256} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="card">
              <h3 className="card-title" style={{ marginBottom: 14 }}>Profile</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Display Name</label>
                  <input className="input" defaultValue="Karthik" />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Email</label>
                  <input className="input" type="email" defaultValue="" placeholder="your@email.com" />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Preferred Framework</label>
                  <select className="input" style={{ cursor: 'pointer' }}>
                    <option>React (Next.js)</option>
                    <option>Vue (Nuxt)</option>
                    <option>Svelte (SvelteKit)</option>
                    <option>Angular</option>
                    <option>Vanilla HTML/CSS/JS</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Appearance Tab */}
          {activeTab === 'appearance' && (
            <div className="card">
              <h3 className="card-title" style={{ marginBottom: 14 }}>Appearance</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Theme</label>
                  <select className="input" style={{ cursor: 'pointer' }}>
                    <option>Light (Default)</option>
                    <option>Dark</option>
                    <option>System</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Editor Font Size</label>
                  <input className="input" type="number" defaultValue={14} min={10} max={20} />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Accent Color</label>
                  <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                    {['#6366F1', '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EC4899'].map(c => (
                      <div key={c} style={{
                        width: 28, height: 28, borderRadius: '50%', background: c, cursor: 'pointer',
                        border: c === '#6366F1' ? '2px solid var(--text-primary)' : '2px solid transparent',
                      }} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Memory Tab */}
          {activeTab === 'memory' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="card">
                <h3 className="card-title" style={{ marginBottom: 14 }}>NEURON-X Memory</h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>
                  Manage your persistent memory. Clearing memory will reset all learning.
                </p>
                <div style={{ display: 'flex', gap: 12 }}>
                  <button className="btn btn-secondary btn-sm">Export Memory</button>
                  <button className="btn btn-secondary btn-sm">Import Memory</button>
                  <button className="btn btn-danger btn-sm">Clear All Memory</button>
                </div>
              </div>
              <div className="card">
                <h3 className="card-title" style={{ marginBottom: 14 }}>Memory Settings</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {[
                    { label: 'Auto-learn preferences', desc: 'Detect and store coding style preferences' },
                    { label: 'Store bug patterns', desc: 'Remember past bugs to prevent recurrence' },
                    { label: 'Cross-project memory', desc: 'Share learnings across all projects' },
                  ].map(s => (
                    <div key={s.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0' }}>
                      <div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>{s.label}</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{s.desc}</div>
                      </div>
                      <label style={{ position: 'relative', width: 36, height: 20, cursor: 'pointer' }}>
                        <input type="checkbox" defaultChecked style={{ opacity: 0, width: 0, height: 0 }} />
                        <span style={{
                          position: 'absolute', inset: 0, borderRadius: 10,
                          background: 'var(--brand)', transition: 'all 200ms',
                        }}>
                          <span style={{
                            position: 'absolute', width: 16, height: 16, borderRadius: '50%',
                            background: 'white', top: 2, left: 18, transition: 'all 200ms',
                          }} />
                        </span>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
