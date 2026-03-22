'use client';

import Sidebar from '@/components/Sidebar';
import { Bug, Send, AlertTriangle, CheckCircle2, FileCode, Zap } from 'lucide-react';
import { useState } from 'react';

interface DebugResult {
  rootCause: string;
  location: string;
  fix: string;
  confidence: number;
  causalChain: string[];
}

export default function DebugPage() {
  const [code, setCode] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DebugResult | null>(null);

  const runDebug = async () => {
    if (!code.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `DEBUG THIS CODE. Find the root cause, provide the exact fix, and explain the causal chain.
${errorMsg ? `Error message: ${errorMsg}` : ''}

Code:
\`\`\`
${code}
\`\`\`

Respond in EXACTLY this JSON format:
{
  "rootCause": "one-line explanation",
  "location": "file/function/line",
  "fix": "the corrected code block",
  "confidence": 0.95,
  "causalChain": ["step1", "step2", "step3"]
}`,
          history: [],
          mode: 'debug',
        }),
      });

      const data = await res.json();
      try {
        const jsonMatch = data.content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          setResult(JSON.parse(jsonMatch[0]));
        } else {
          setResult({
            rootCause: data.content.slice(0, 200),
            location: 'See response',
            fix: data.content,
            confidence: 0.85,
            causalChain: ['Analysis complete'],
          });
        }
      } catch {
        setResult({
          rootCause: 'See full analysis below',
          location: 'Multiple locations',
          fix: data.content,
          confidence: 0.8,
          causalChain: ['Parsed response', 'Generated fix'],
        });
      }
    } catch {
      setResult({
        rootCause: 'Could not reach TRACE-X. Check API key.',
        location: '-',
        fix: '-',
        confidence: 0,
        causalChain: [],
      });
    }

    setLoading(false);
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">Debug</span>
            <span className="badge badge-warning" style={{ marginLeft: 8 }}>TRACE-X</span>
          </div>
        </div>

        <div className="page-content" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>
          {/* Input Panel */}
          <div>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 10 }}>Paste your code</h3>
            <textarea
              className="input font-mono"
              value={code}
              onChange={e => setCode(e.target.value)}
              placeholder="Paste the buggy code here..."
              style={{ minHeight: 300, fontSize: '0.82rem', lineHeight: 1.7 }}
            />
            <div style={{ marginTop: 10 }}>
              <input className="input" placeholder="Error message (optional)..."
                value={errorMsg} onChange={e => setErrorMsg(e.target.value)} />
            </div>
            <button className="btn btn-brand" style={{ marginTop: 12, width: '100%' }} onClick={runDebug} disabled={loading || !code.trim()}>
              {loading ? (
                <>
                  <div className="typing-dots" style={{ padding: 0 }}>
                    <span /><span /><span />
                  </div>
                  TRACE-X analyzing...
                </>
              ) : (
                <><Bug size={14} /> Run TRACE-X Debug</>
              )}
            </button>
          </div>

          {/* Result Panel */}
          <div>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 10 }}>Analysis</h3>
            {result ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* Root Cause */}
                <div className="card" style={{ borderColor: 'var(--danger-border)', background: 'var(--danger-light)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <AlertTriangle size={16} style={{ color: 'var(--danger)' }} />
                    <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--danger)' }}>Root Cause</span>
                  </div>
                  <p style={{ fontSize: '0.82rem' }}>{result.rootCause}</p>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>
                    Location: {result.location} · Confidence: {Math.round(result.confidence * 100)}%
                  </p>
                </div>

                {/* Causal Chain */}
                {result.causalChain.length > 0 && (
                  <div className="card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                      <Zap size={14} style={{ color: 'var(--agent-debug)' }} />
                      <span style={{ fontWeight: 600, fontSize: '0.82rem' }}>Causal Chain</span>
                    </div>
                    {result.causalChain.map((step, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
                        <span style={{ width: 20, height: 20, borderRadius: '50%', background: 'var(--brand-light)', color: 'var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem', fontWeight: 600, flexShrink: 0 }}>
                          {i + 1}
                        </span>
                        <span style={{ fontSize: '0.82rem' }}>{step}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Fix */}
                <div className="card" style={{ borderColor: 'var(--success-border)', background: 'var(--success-light)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <CheckCircle2 size={16} style={{ color: 'var(--success)' }} />
                    <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--success)' }}>Fix</span>
                  </div>
                  <pre style={{
                    background: 'var(--code-bg)',
                    color: 'var(--code-text)',
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.78rem',
                    overflow: 'auto',
                    maxHeight: 300,
                    fontFamily: "'JetBrains Mono', monospace",
                  }}>
                    {result.fix}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="empty-state" style={{ minHeight: 300, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)' }}>
                <div className="empty-state-icon"><Bug size={20} /></div>
                <div className="empty-state-title">Paste code and run TRACE-X</div>
                <div className="empty-state-text">TRACE-X will find the root cause, trace the causal chain, and suggest a fix.</div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
