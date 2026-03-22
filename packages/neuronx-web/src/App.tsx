import React, { useState, useEffect, useRef, useCallback } from 'react';
import * as api from './api';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Types
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

type View = 'dashboard' | 'chat' | 'memories' | 'recall' | 'bonds' | 'zones' | 'nrnlang' | 'events' | 'export' | 'settings';

interface Stats {
  brain_name: string;
  total_engrams: number;
  total_axons: number;
  session_engrams: number;
  interaction_count: number;
  zone_counts: Record<string, number>;
}

interface NEvent {
  type: string;
  data: Record<string, unknown>;
  timestamp: number;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Nav Items
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

const NAV_ITEMS: { section: string; items: { id: View; icon: string; label: string }[] }[] = [
  {
    section: 'CORE',
    items: [
      { id: 'dashboard', icon: '⬡', label: 'Dashboard' },
      { id: 'chat', icon: '⌘', label: 'Chat Engine' },
      { id: 'memories', icon: '◈', label: 'Memories' },
      { id: 'recall', icon: '⊙', label: 'Recall' },
      { id: 'bonds', icon: '⋈', label: 'Bonds' },
      { id: 'zones', icon: '◎', label: 'Thermal Zones' },
    ],
  },
  {
    section: 'TOOLS',
    items: [
      { id: 'nrnlang', icon: '⌘', label: 'NRNLANG-Ω' },
      { id: 'events', icon: '◉', label: 'Live Events' },
      { id: 'export', icon: '⬡', label: 'Export' },
    ],
  },
  {
    section: 'SYSTEM',
    items: [
      { id: 'settings', icon: '⚙', label: 'Settings' },
    ],
  },
];

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Main App
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

export default function App() {
  const [view, setView] = useState<View>('dashboard');
  const [config, setConfig] = useState(() => {
    const saved = localStorage.getItem('neuronx_config');
    return saved ? JSON.parse(saved) : { apiUrl: 'http://localhost:8000', brainName: 'default', provider: 'openai', apiKey: '', model: 'gpt-4o' };
  });
  const [configured, setConfigured] = useState(() => !!localStorage.getItem('neuronx_config'));

  const saveConfig = (cfg: typeof config) => {
    localStorage.setItem('neuronx_config', JSON.stringify(cfg));
    setConfig(cfg);
    setConfigured(true);
  };

  if (!configured) {
    return <SetupScreen config={config} onSave={saveConfig} />;
  }

  return (
    <div className="app">
      <Sidebar view={view} onNavigate={setView} />
      <div className="main-content">
        {view === 'dashboard' && <DashboardView />}
        {view === 'chat' && <ChatView config={config} />}
        {view === 'memories' && <MemoriesView />}
        {view === 'recall' && <RecallView />}
        {view === 'bonds' && <BondsView />}
        {view === 'zones' && <ZonesView />}
        {view === 'nrnlang' && <NRNLangView />}
        {view === 'events' && <EventsView />}
        {view === 'export' && <ExportView />}
        {view === 'settings' && <SettingsView config={config} onSave={saveConfig} />}
      </div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Setup Screen (BUG-011 FIX)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function SetupScreen({ config, onSave }: { config: any; onSave: (c: any) => void }) {
  const [url, setUrl] = useState(config.apiUrl || 'http://localhost:8000');
  const [brain, setBrain] = useState(config.brainName || 'default');
  const [provider, setProvider] = useState(config.provider || 'openai');
  const [apiKey, setApiKey] = useState(config.apiKey || '');
  const [model, setModel] = useState(config.model || 'gpt-4o');

  const models = provider === 'openai' 
    ? ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo']
    : provider === 'anthropic'
    ? ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307']
    : ['moonshotai/kimi-k2-instruct', 'meta/llama3-70b-instruct'];

  return (
    <div className="setup-screen">
      <div className="setup-card animate-in" style={{ maxWidth: 540 }}>
        <h2>NEURON-X Omega</h2>
        <p>Configure your connection to the memory server and AI Provider.</p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="form-group">
            <label className="form-label">API Server URL</label>
            <input className="form-input" value={url} onChange={e => setUrl(e.target.value)} placeholder="http://localhost:8000" />
          </div>
          <div className="form-group">
            <label className="form-label">Brain Name</label>
            <input className="form-input" value={brain} onChange={e => setBrain(e.target.value)} placeholder="default" />
          </div>
        </div>
        
        <div style={{ marginTop: 16, marginBottom: 16, borderTop: '1px solid var(--border-color)', paddingTop: 16 }}>
          <div className="form-group">
            <label className="form-label">AI Provider</label>
            <select className="form-input" value={provider} onChange={e => { setProvider(e.target.value); setModel(e.target.value === 'openai' ? 'gpt-4o' : e.target.value === 'anthropic' ? 'claude-3-opus-20240229' : 'moonshotai/kimi-k2-instruct'); }}>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="nvidia">NVIDIA NIM</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">API Key</label>
            <input type="password" className="form-input" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder={`Enter ${provider} API Key`} />
          </div>
          <div className="form-group">
            <label className="form-label">Model Selection</label>
            <select className="form-input" value={model} onChange={e => setModel(e.target.value)}>
              {models.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        </div>
        
        <button className="btn btn-primary" style={{ width: '100%', marginTop: 8 }} onClick={() => onSave({ apiUrl: url, brainName: brain, provider, apiKey, model })}>
          Connect & Initialize
        </button>
      </div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Sidebar
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function Sidebar({ view, onNavigate }: { view: View; onNavigate: (v: View) => void }) {
  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <h1>NEURON-X Ω</h1>
        <div className="version">v1.0.0 — omega</div>
      </div>
      <div className="sidebar-nav">
        {NAV_ITEMS.map(section => (
          <div key={section.section} className="nav-section">
            <div className="nav-section-title">{section.section}</div>
            {section.items.map(item => (
              <button key={item.id} className={`nav-item ${view === item.id ? 'active' : ''}`} onClick={() => onNavigate(item.id)}>
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
        ))}
      </div>
    </nav>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Dashboard View
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function DashboardView() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [input, setInput] = useState('');
  const [result, setResult] = useState<string>('');

  useEffect(() => {
    api.brainStats().then(setStats).catch(() => setStats(null));
  }, []);

  const handleRemember = async () => {
    if (!input.trim()) return;
    try {
      const res = await api.brainRemember(input);
      setResult(`${res.action} → ${res.engram_id?.slice(0, 8)}… (surprise: ${res.surprise_score?.toFixed(2)})`);
      setInput('');
      api.brainStats().then(setStats);
    } catch (e: any) { setResult(`Error: ${e.message}`); }
  };

  const zoneTotal = stats ? Object.values(stats.zone_counts).reduce((a, b) => a + b, 0) : 0;

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>NEURON-X Omega — Memory Control Center</p>
      </div>
      <div className="page-body">
        <div className="chat-input-wrapper">
          <input className="chat-input" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleRemember()} placeholder="Store a memory…" />
          <button className="btn btn-primary" onClick={handleRemember}>Remember</button>
        </div>
        {result && <div className="card" style={{ marginBottom: 16 }}><code className="mono">{result}</code></div>}

        {stats && (
          <>
            <div className="stats-grid">
              <div className="stat-card"><div className="stat-label">Total Memories</div><div className="stat-value cyan">{stats.total_engrams}</div></div>
              <div className="stat-card"><div className="stat-label">Total Bonds</div><div className="stat-value purple">{stats.total_axons}</div></div>
              <div className="stat-card"><div className="stat-label">Session Stored</div><div className="stat-value green">{stats.session_engrams}</div></div>
              <div className="stat-card"><div className="stat-label">Interactions</div><div className="stat-value amber">{stats.interaction_count}</div></div>
            </div>

            <div className="card">
              <div className="card-header">
                <span className="card-title">Thermal Zones</span>
                <span className="card-subtitle">{zoneTotal} Total</span>
              </div>
              {zoneTotal > 0 && (
                <div className="zone-bar">
                  {(['HOT', 'WARM', 'COLD', 'SILENT'] as const).map(z => {
                    const pct = ((stats.zone_counts[z] || 0) / zoneTotal) * 100;
                    return pct > 0 ? <div key={z} className={`zone-bar-segment ${z}`} style={{ width: `${pct}%` }}>{stats.zone_counts[z]}</div> : null;
                  })}
                </div>
              )}
            </div>
          </>
        )}
        {!stats && <div className="card"><p style={{ color: 'var(--text-tertiary)' }}>Connect to the API server to see stats.</p></div>}
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Chat View
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function ChatView({ config }: { config: any }) {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant' | 'system', content: string, memories?: number }>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !config.apiKey) return;
    
    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await api.brainChat(userMessage, config.provider, config.apiKey, config.model);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: res.response,
        memories: res.context_memories 
      }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'system', content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <h2>Chat Engine</h2>
        <p>Interact with {config.model} powered by NEURON-X Memory</p>
      </div>
      <div className="page-body" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 180px)' }}>
        {!config.apiKey ? (
          <div className="card" style={{ border: '1px solid var(--danger)' }}>
            <h3 style={{ color: 'var(--danger)', marginBottom: 8 }}>API Key Missing</h3>
            <p>Please configure your <strong>{config.provider}</strong> API key in the System Settings to use the Chat Engine.</p>
          </div>
        ) : (
          <>
            <div className="card" style={{ flex: 1, overflowY: 'auto', marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
              {messages.length === 0 ? (
                <div style={{ margin: 'auto', color: 'var(--text-tertiary)', textAlign: 'center' }}>
                  <div style={{ fontSize: 24, marginBottom: 8 }}>🧠</div>
                  Send a message to begin.
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div key={idx} style={{
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '80%',
                    background: msg.role === 'user' ? 'var(--primary)' : msg.role === 'system' ? 'var(--danger)' : 'var(--bg-secondary)',
                    color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                    padding: '12px 16px',
                    borderRadius: 8,
                    border: msg.role === 'user' ? 'none' : '1px solid var(--border-color)',
                  }}>
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{msg.content}</div>
                    {msg.memories !== undefined && msg.memories > 0 && (
                      <div style={{ fontSize: 10, marginTop: 8, opacity: 0.7, fontFamily: 'var(--font-mono)' }}>
                        ◈ {msg.memories} memories injected
                      </div>
                    )}
                  </div>
                ))
              )}
              {loading && (
                <div style={{ alignSelf: 'flex-start', padding: '12px 16px', color: 'var(--text-tertiary)' }}>
                  <span className="blink">●</span> Thinking...
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            <div className="chat-input-wrapper" style={{ marginBottom: 0 }}>
              <input 
                className="chat-input" 
                value={input} 
                onChange={e => setInput(e.target.value)} 
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()} 
                placeholder="Ask your brain..." 
                disabled={loading}
              />
              <button className="btn btn-primary" onClick={handleSend} disabled={loading || !input.trim()}>
                Send
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Memories View
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function MemoriesView() {
  const [memories, setMemories] = useState<any[]>([]);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);

  const load = useCallback(() => {
    api.listMemories(page, 20).then(r => { setMemories(r.memories || []); setTotal(r.total || 0); }).catch(() => {});
  }, [page]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id: string) => {
    try { await api.deleteMemory(id); load(); } catch {}
  };

  return (
    <>
      <div className="page-header">
        <h2>Memories</h2>
        <p>{total} engrams stored — page {page + 1}</p>
      </div>
      <div className="page-body">
        <div className="engram-list">
          {memories.map((m: any) => (
            <div key={m.id} className="engram-card animate-in">
              <div className={`engram-zone ${m.zone}`} />
              <div className="engram-content">
                <div className="engram-text">{m.raw}</div>
                <div className="engram-meta">
                  <span>{m.zone}</span>
                  <span>conf:{m.confidence?.toFixed(2)}</span>
                  <span>{m.decay_class}</span>
                  <span>{m.emotion}</span>
                  {m.is_anchor && <span className="engram-anchor">◆ ANCHOR</span>}
                  <span>seen:{m.access_count}×</span>
                </div>
              </div>
              <button className="btn btn-danger" onClick={() => handleDelete(m.id)} style={{ fontSize: 11, padding: '4px 8px' }}>×</button>
            </div>
          ))}
          {memories.length === 0 && <div className="card"><p style={{ color: 'var(--text-tertiary)' }}>No memories yet. Store something first!</p></div>}
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <button className="btn btn-secondary" disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Prev</button>
          <button className="btn btn-secondary" disabled={memories.length < 20} onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Recall View
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function RecallView() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);

  const handleRecall = async () => {
    if (!query.trim()) return;
    try {
      const res = await api.brainRecall(query, 10);
      setResults(res.results || []);
    } catch {}
  };

  return (
    <>
      <div className="page-header">
        <h2>Recall</h2>
        <p>Query your memories with WSRA-X scoring</p>
      </div>
      <div className="page-body">
        <div className="chat-input-wrapper">
          <input className="chat-input" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleRecall()} placeholder="What do you want to remember?" />
          <button className="btn btn-primary" onClick={handleRecall}>Recall</button>
        </div>
        <div className="engram-list">
          {results.map((r: any, i: number) => (
            <div key={r.id} className="engram-card animate-in" style={{ animationDelay: `${i * 50}ms` }}>
              <div className={`engram-zone ${r.zone}`} />
              <div className="engram-content">
                <div className="engram-text">{r.raw}</div>
                <div className="engram-meta">
                  <span style={{ color: 'var(--accent-cyan)' }}>score:{r.score?.toFixed(3)}</span>
                  <span>conf:{r.confidence?.toFixed(2)}</span>
                  <span>{r.zone}</span>
                  <span>{r.emotion}</span>
                  <span>{r.age_days?.toFixed(0)}d old</span>
                  {r.is_anchor && <span className="engram-anchor">◆ ANCHOR</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Bonds View
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function BondsView() {
  const [bonds, setBonds] = useState<any[]>([]);

  useEffect(() => {
    api.listBonds().then(r => setBonds(r.bonds || [])).catch(() => {});
  }, []);

  const typeNames: Record<number, string> = { 0: 'TIME', 1: 'WORD', 2: 'EMOTION', 3: 'CLASH', 4: 'HERALD' };

  return (
    <>
      <div className="page-header">
        <h2>Bonds</h2>
        <p>{bonds.length} axon connections between memories</p>
      </div>
      <div className="page-body">
        <div className="engram-list">
          {bonds.map((b: any, i: number) => (
            <div key={i} className="engram-card animate-in">
              <div className="engram-content">
                <div className="engram-meta">
                  <span style={{ color: 'var(--accent-cyan)' }}>{b.from_id?.slice(0, 8)}…</span>
                  <span>→</span>
                  <span style={{ color: 'var(--accent-purple)' }}>{b.to_id?.slice(0, 8)}…</span>
                  <span>synapse:{b.synapse?.toFixed(3)}</span>
                  <span>{typeNames[b.axon_type] || `type:${b.axon_type}`}</span>
                </div>
              </div>
            </div>
          ))}
          {bonds.length === 0 && <div className="card"><p style={{ color: 'var(--text-tertiary)' }}>No bonds yet.</p></div>}
        </div>
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Zones View
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function ZonesView() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [auditResult, setAuditResult] = useState<any>(null);

  useEffect(() => { api.brainStats().then(setStats).catch(() => {}); }, []);

  const handleAudit = async () => {
    try {
      const r = await api.brainAudit();
      setAuditResult(r);
      api.brainStats().then(setStats);
    } catch {}
  };

  const zones = stats?.zone_counts || {};
  const total = Object.values(zones).reduce((a, b) => a + b, 0);

  return (
    <>
      <div className="page-header">
        <h2>Thermal Zones</h2>
        <p>Memory heat map — HOT → WARM → COLD → SILENT</p>
      </div>
      <div className="page-body">
        <div className="stats-grid">
          <div className="stat-card"><div className="stat-label">🔥 Hot</div><div className="stat-value red">{zones.HOT || 0}</div></div>
          <div className="stat-card"><div className="stat-label">🌡 Warm</div><div className="stat-value amber">{zones.WARM || 0}</div></div>
          <div className="stat-card"><div className="stat-label">❄ Cold</div><div className="stat-value cyan">{zones.COLD || 0}</div></div>
          <div className="stat-card"><div className="stat-label">👻 Silent</div><div className="stat-value" style={{ color: 'var(--zone-silent)' }}>{zones.SILENT || 0}</div></div>
        </div>

        {total > 0 && (
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-title">Zone Distribution</div>
            <div className="zone-bar" style={{ height: 32 }}>
              {(['HOT', 'WARM', 'COLD', 'SILENT'] as const).map(z => {
                const pct = ((zones[z] || 0) / total) * 100;
                return pct > 0 ? <div key={z} className={`zone-bar-segment ${z}`} style={{ width: `${pct}%` }}>{z} {zones[z]}</div> : null;
              })}
            </div>
          </div>
        )}

        <button className="btn btn-primary" onClick={handleAudit} style={{ marginBottom: 16 }}>Run Audit</button>

        {auditResult && (
          <div className="card animate-in">
            <div className="card-title">Audit Results</div>
            <div className="engram-meta" style={{ marginTop: 8 }}>
              <span>promoted:{auditResult.promoted}</span>
              <span>demoted:{auditResult.demoted}</span>
              <span>reawakened:{auditResult.reawakened}</span>
              <span>fossilized:{auditResult.fossilized}</span>
              <span>crystallized:{auditResult.crystallized}</span>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// NRNLANG-Ω Console (BUG-017)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function NRNLangView() {
  const [cmd, setCmd] = useState('');
  const [history, setHistory] = useState<{ input: string; output: string; type: string }[]>([]);
  const consoleRef = useRef<HTMLDivElement>(null);

  const execute = async () => {
    if (!cmd.trim()) return;
    try {
      const res = await api.executeNRNLang(cmd);
      const output = res.log || JSON.stringify(res, null, 2);
      setHistory(h => [...h, { input: cmd, output, type: res.status === 'error' ? 'error' : 'success' }]);
    } catch (e: any) {
      setHistory(h => [...h, { input: cmd, output: e.message, type: 'error' }]);
    }
    setCmd('');
    setTimeout(() => consoleRef.current?.scrollTo(0, consoleRef.current.scrollHeight), 50);
  };

  return (
    <>
      <div className="page-header">
        <h2>NRNLANG-Ω Console</h2>
        <p>Execute memory commands in the NEURON-X language</p>
      </div>
      <div className="page-body">
        <div className="nrnlang-console" ref={consoleRef}>
          <div className="nrnlang-line action">╔═══ NRNLANG-Ω Interpreter v1.0 ═══╗</div>
          <div className="nrnlang-line">Commands: FORGE, ECHO, RECALL, AUDIT, STATS, EXPORT, EXPIRE, CRYSTALLIZE</div>
          <div className="nrnlang-line">───────────────────────────────────</div>
          {history.map((h, i) => (
            <React.Fragment key={i}>
              <div className="nrnlang-line action">⊕ {h.input}</div>
              <div className={`nrnlang-line ${h.type}`}>{h.output}</div>
            </React.Fragment>
          ))}
        </div>
        <div className="chat-input-wrapper" style={{ marginTop: 12 }}>
          <input className="chat-input" value={cmd} onChange={e => setCmd(e.target.value)} onKeyDown={e => e.key === 'Enter' && execute()} placeholder='FORGE engram("I love pizza")' style={{ fontFamily: 'var(--font-mono)' }} />
          <button className="btn btn-primary" onClick={execute}>Execute</button>
        </div>
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Live Events (BUG-016/019)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function EventsView() {
  const [events, setEvents] = useState<NEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  const toggle = () => {
    if (connected && esRef.current) {
      esRef.current.close();
      esRef.current = null;
      setConnected(false);
    } else {
      esRef.current = api.connectSSE((ev: NEvent) => {
        if (ev.type !== 'heartbeat') {
          setEvents(prev => [ev, ...prev.slice(0, 99)]);
        }
      });
      setConnected(true);
    }
  };

  useEffect(() => () => { esRef.current?.close(); }, []);

  return (
    <>
      <div className="page-header">
        <h2>Live Events</h2>
        <p>Real-time SSE stream of all brain activity</p>
      </div>
      <div className="page-body">
        <button className={`btn ${connected ? 'btn-danger' : 'btn-primary'}`} onClick={toggle} style={{ marginBottom: 16 }}>
          {connected ? '● Disconnect' : '○ Connect'}
        </button>
        <div className="event-feed">
          {events.map((ev, i) => (
            <div key={i} className="event-item animate-in">
              <div className={`event-dot ${ev.type}`} />
              <span className="event-time">{new Date(ev.timestamp * 1000).toLocaleTimeString()}</span>
              <span className="event-text">{ev.type}: {JSON.stringify(ev.data)}</span>
            </div>
          ))}
          {events.length === 0 && <div style={{ color: 'var(--text-tertiary)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{connected ? 'Waiting for events…' : 'Click connect to start streaming.'}</div>}
        </div>
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Export View (BUG-018)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function ExportView() {
  const [output, setOutput] = useState('');
  const [format, setFormat] = useState('json');

  const handleExport = async () => {
    try {
      const data = await api.exportBrain(format);
      setOutput(data);
    } catch (e: any) { setOutput(`Error: ${e.message}`); }
  };

  return (
    <>
      <div className="page-header">
        <h2>Export</h2>
        <p>Export your brain in multiple formats</p>
      </div>
      <div className="page-body">
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          {['json', 'markdown', 'csv', 'nrnlang'].map(f => (
            <button key={f} className={`btn ${format === f ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFormat(f)}>
              {f.toUpperCase()}
            </button>
          ))}
          <button className="btn btn-primary" onClick={handleExport}>Export</button>
        </div>
        {output && (
          <div className="nrnlang-console">
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 11 }}>{output}</pre>
          </div>
        )}
      </div>
    </>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Settings View (BUG-011)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━

function SettingsView({ config, onSave }: { config: any; onSave: (c: any) => void }) {
  const [url, setUrl] = useState(config.apiUrl);
  const [brain, setBrain] = useState(config.brainName);
  const [provider, setProvider] = useState(config.provider || 'openai');
  const [apiKey, setApiKey] = useState(config.apiKey || '');
  const [model, setModel] = useState(config.model || 'gpt-4o');

  const models = provider === 'openai' 
    ? ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo']
    : provider === 'anthropic'
    ? ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307']
    : ['moonshotai/kimi-k2-instruct', 'meta/llama3-70b-instruct'];

  return (
    <>
      <div className="page-header">
        <h2>Settings</h2>
        <p>Configure your NEURON-X connection</p>
      </div>
      <div className="page-body">
        <div className="card" style={{ maxWidth: 500 }}>
          <div className="form-group">
            <label className="form-label">API Server URL</label>
            <input className="form-input" value={url} onChange={e => setUrl(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Brain Name</label>
            <input className="form-input" value={brain} onChange={e => setBrain(e.target.value)} />
          </div>
          
          <div style={{ marginTop: 24, marginBottom: 24, borderTop: '1px solid var(--border-color)', paddingTop: 24 }}>
            <h3 style={{ fontSize: 13, marginBottom: 16, color: 'var(--text-primary)' }}>AI Provider Configuration</h3>
            <div className="form-group">
              <label className="form-label">Provider</label>
              <select className="form-input" value={provider} onChange={e => { setProvider(e.target.value); setModel(e.target.value === 'openai' ? 'gpt-4o' : e.target.value === 'anthropic' ? 'claude-3-opus-20240229' : 'moonshotai/kimi-k2-instruct'); }}>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="nvidia">NVIDIA NIM</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">API Key</label>
              <input type="password" className="form-input" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder={`Enter ${provider} API Key`} />
            </div>
            <div className="form-group">
              <label className="form-label">Model Selection</label>
              <select className="form-input" value={model} onChange={e => setModel(e.target.value)}>
                {models.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={() => onSave({ apiUrl: url, brainName: brain, provider, apiKey, model })}>Save Settings</button>
            <button className="btn btn-danger" onClick={() => { localStorage.removeItem('neuronx_config'); window.location.reload(); }}>Full Reset</button>
          </div>
          <div style={{ marginTop: 16, fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
            <p>NEURON-X Omega v1.0.0</p>
            <p>Settings uniquely persisted to localStorage (BUG-011 fix)</p>
          </div>
        </div>
      </div>
    </>
  );
}
