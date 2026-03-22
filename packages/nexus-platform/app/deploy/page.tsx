'use client';

import Sidebar from '@/components/Sidebar';
import { Rocket, Globe, Cloud, Server, ChevronRight, CheckCircle2, AlertCircle, ExternalLink } from 'lucide-react';
import { useState } from 'react';

const PLATFORMS = [
  { id: 'vercel', name: 'Vercel', desc: 'Optimal for Next.js. Zero config.', icon: '▲', recommended: true },
  { id: 'netlify', name: 'Netlify', desc: 'Fast CDN with forms and functions.', icon: '◆' },
  { id: 'cloudflare', name: 'Cloudflare Pages', desc: 'Edge-first performance.', icon: '☁' },
  { id: 'railway', name: 'Railway', desc: 'Full stack with database.', icon: '🚂' },
  { id: 'docker', name: 'Docker', desc: 'Container-based deploy.', icon: '🐳' },
  { id: 'zip', name: 'Export ZIP', desc: 'Download full source.', icon: '📦' },
];

type Step = 'platform' | 'config' | 'deploying' | 'done';

export default function DeployPage() {
  const [step, setStep] = useState<Step>('platform');
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [deployProgress, setDeployProgress] = useState(0);

  const startDeploy = () => {
    setStep('deploying');
    setDeployProgress(0);
    const interval = setInterval(() => {
      setDeployProgress(p => {
        if (p >= 100) {
          clearInterval(interval);
          setStep('done');
          return 100;
        }
        return p + Math.random() * 15;
      });
    }, 500);
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">Deploy</span>
            <span className="badge badge-brand" style={{ marginLeft: 8 }}>
              <Rocket size={10} /> DEPLOY Agent
            </span>
          </div>
        </div>

        <div className="page-content" style={{ maxWidth: 700, margin: '0 auto' }}>
          {/* Progress Steps */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
            {(['platform', 'config', 'deploying', 'done'] as Step[]).map((s, i) => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: step === s ? 'var(--brand)' : i < ['platform', 'config', 'deploying', 'done'].indexOf(step) ? 'var(--success)' : 'var(--bg-tertiary)',
                  color: step === s || i < ['platform', 'config', 'deploying', 'done'].indexOf(step) ? 'white' : 'var(--text-muted)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.72rem', fontWeight: 600,
                }}>
                  {i < ['platform', 'config', 'deploying', 'done'].indexOf(step) ? '✓' : i + 1}
                </div>
                <span style={{ fontSize: '0.78rem', fontWeight: step === s ? 600 : 400, color: step === s ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                  {s === 'platform' ? 'Platform' : s === 'config' ? 'Configure' : s === 'deploying' ? 'Deploying' : 'Live'}
                </span>
                {i < 3 && <span style={{ width: 32, height: 1, background: 'var(--border)' }} />}
              </div>
            ))}
          </div>

          {/* Platform Selection */}
          {step === 'platform' && (
            <div>
              <h2 className="page-title">Choose deployment platform</h2>
              <p className="page-subtitle">Select where you want to deploy your project.</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                {PLATFORMS.map(p => (
                  <div key={p.id} className={`card`}
                    style={{
                      cursor: 'pointer', padding: '18px 20px',
                      borderColor: selectedPlatform === p.id ? 'var(--brand)' : undefined,
                      background: selectedPlatform === p.id ? 'var(--brand-light)' : undefined,
                    }}
                    onClick={() => setSelectedPlatform(p.id)}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: '1.3rem' }}>{p.icon}</span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                          {p.name}
                          {p.recommended && <span className="badge badge-brand">Recommended</span>}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{p.desc}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <button className="btn btn-brand" style={{ width: '100%', marginTop: 20 }}
                disabled={!selectedPlatform} onClick={() => setStep('config')}>
                Continue <ChevronRight size={14} />
              </button>
            </div>
          )}

          {/* Configure */}
          {step === 'config' && (
            <div>
              <h2 className="page-title">Configure deployment</h2>
              <p className="page-subtitle">Review settings before deploying.</p>
              <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div>
                    <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Project Name</label>
                    <input className="input" defaultValue="my-nexus-project" />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Branch</label>
                    <input className="input" defaultValue="main" />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4, display: 'block' }}>Environment</label>
                    <select className="input" style={{ cursor: 'pointer' }}>
                      <option>Production</option>
                      <option>Staging</option>
                      <option>Preview</option>
                    </select>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                <button className="btn btn-secondary" onClick={() => setStep('platform')}>Back</button>
                <button className="btn btn-brand" style={{ flex: 1 }} onClick={startDeploy}>
                  <Rocket size={14} /> Deploy Now
                </button>
              </div>
            </div>
          )}

          {/* Deploying */}
          {step === 'deploying' && (
            <div className="card" style={{ textAlign: 'center', padding: 40 }}>
              <div className="typing-dots" style={{ justifyContent: 'center', marginBottom: 16 }}>
                <span /><span /><span />
              </div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>Deploying...</h2>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 20 }}>
                DEPLOY Agent is building and publishing your project.
              </p>
              <div style={{ height: 6, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 'var(--radius-full)',
                  background: 'linear-gradient(90deg, var(--brand), var(--agent-parse))',
                  width: `${Math.min(deployProgress, 100)}%`,
                  transition: 'width 0.5s var(--ease)',
                }} />
              </div>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 8 }}>
                {Math.round(Math.min(deployProgress, 100))}%
              </p>
            </div>
          )}

          {/* Done */}
          {step === 'done' && (
            <div className="card" style={{ textAlign: 'center', padding: 40 }}>
              <CheckCircle2 size={40} style={{ color: 'var(--success)', marginBottom: 16 }} />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 8 }}>Deployed Successfully!</h2>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 20 }}>
                Your project is now live.
              </p>
              <div className="card" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 16px', background: 'var(--success-light)', borderColor: 'var(--success-border)' }}>
                <Globe size={14} style={{ color: 'var(--success)' }} />
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>my-nexus-project.vercel.app</span>
                <ExternalLink size={12} style={{ color: 'var(--text-muted)' }} />
              </div>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 20 }}>
                <button className="btn btn-secondary" onClick={() => { setStep('platform'); setSelectedPlatform(''); }}>
                  Deploy Another
                </button>
                <button className="btn btn-brand" onClick={() => window.open('https://my-nexus-project.vercel.app', '_blank')}>
                  <ExternalLink size={14} /> Visit Site
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
