'use client';

import { useRouter } from 'next/navigation';
import { Zap, ArrowRight, Brain, Shield, Bug, Cpu, Globe, ChevronRight, CheckCircle2 } from 'lucide-react';

export default function Landing() {
  const router = useRouter();

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* NAV */}
      <header className="landing-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="sidebar-brand-icon"><Zap size={14} /></div>
          <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>NEXUS-Ω</span>
        </div>
        <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          <a href="#features" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Features</a>
          <a href="#pricing" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Pricing</a>
          <button className="btn btn-ghost btn-sm" onClick={() => router.push('/dashboard')}>Sign In</button>
          <button className="btn btn-brand btn-sm" onClick={() => router.push('/build')}>
            Start Building Free <ArrowRight size={14} />
          </button>
        </div>
      </header>

      {/* HERO */}
      <section className="landing-hero">
        <div className="landing-badge">
          <span className="pulse-dot" /> Now with 6 autonomous AI agents
        </div>
        <h1 className="landing-h1">
          Build anything.<br />
          <span className="text-gradient">Ship everything.</span><br />
          Forget nothing.
        </h1>
        <p className="landing-sub">
          The vibe coding platform with a permanent brain. Faster than Lovable.
          Smarter than Bolt. Grows with every project you build.
        </p>
        <div className="landing-ctas">
          <button className="btn btn-brand btn-lg" onClick={() => router.push('/build')}>
            Start Building Free <ArrowRight size={16} />
          </button>
          <button className="btn btn-secondary btn-lg" onClick={() => {
            document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
          }}>
            See how it works
          </button>
        </div>
      </section>

      {/* PROBLEMS */}
      <section className="landing-section">
        <h2 className="landing-section-title">What's broken with existing platforms</h2>
        <p className="landing-section-sub">Every vibe coding platform today shares the same fatal flaws.</p>
        <div className="problem-grid">
          {[
            { stat: '100%', title: 'Lovable forgets you', desc: 'Every session starts from zero. Your preferences, bugs, patterns — all gone.' },
            { stat: '50+', title: 'Bolt breaks at scale', desc: 'Code quality degrades after 50 prompts. Users spend $1,000+ on token fixes.' },
            { stat: '170/1645', title: 'None of them are secure', desc: 'Apps with security holes. No scoring, no checks, no protection.' },
          ].map(p => (
            <div className="problem-card" key={p.title}>
              <div className="problem-stat">{p.stat}</div>
              <div className="feature-title">{p.title}</div>
              <div className="feature-desc" style={{ color: 'var(--danger)' }}>{p.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section className="landing-section" id="features">
        <h2 className="landing-section-title">We built the brain that nobody else has.</h2>
        <p className="landing-section-sub">6 autonomous AI agents working in parallel. Permanent memory. Context that never degrades.</p>
        <div className="features-grid">
          {[
            { icon: <Brain size={20} />, bg: 'var(--brand-light)', color: 'var(--brand)', title: 'Permanent Memory', desc: 'Remembers your style, bugs, preferences. Forever. Session 100 is smarter than Session 1.' },
            { icon: <Shield size={20} />, bg: 'var(--success-light)', color: 'var(--success)', title: 'Security Shield', desc: 'Every line scored 0-100 before you see it. SECUREGEN-X blocks vulnerabilities automatically.' },
            { icon: <Bug size={20} />, bg: 'var(--warning-light)', color: 'var(--warning)', title: 'Causal Debug', desc: 'TRACE-X finds WHY bugs happen, not just where. Stores patterns to prevent recurrence.' },
            { icon: <Cpu size={20} />, bg: '#F3E8FF', color: 'var(--agent-parse)', title: '6 AI Agents', desc: 'PARSE → ARCHITECT → BUILD → SECURE → DEBUG → DEPLOY — all working in parallel.' },
            { icon: <Zap size={20} />, bg: '#FFF7ED', color: '#EA580C', title: '10x Faster', desc: 'Powered by Groq at 800 tokens/sec. Faster than Lovable, Bolt, and v0 combined.' },
            { icon: <Globe size={20} />, bg: 'var(--info-light)', color: 'var(--info)', title: 'Any Backend', desc: 'Supabase, PostgreSQL, MySQL, MongoDB. Zero lock-in. Your choice.' },
          ].map(f => (
            <div className="feature-card" key={f.title}>
              <div className="feature-icon" style={{ background: f.bg, color: f.color }}>{f.icon}</div>
              <div className="feature-title">{f.title}</div>
              <div className="feature-desc">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* SPEED COMPARISON */}
      <section className="landing-section" style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-2xl)', maxWidth: 900, margin: '0 auto 64px', padding: '48px 40px' }}>
        <h2 className="landing-section-title">Groq makes it 10x faster</h2>
        <p className="landing-section-sub" style={{ marginBottom: 32 }}>800 tokens/sec vs 80. The difference is instant.</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[
            { name: 'Lovable', speed: 10, label: '~80 t/s (Claude)' },
            { name: 'Bolt', speed: 12, label: '~95 t/s (OpenAI)' },
            { name: 'v0', speed: 11, label: '~85 t/s (Claude)' },
            { name: 'NEXUS-Ω', speed: 100, label: '~800 t/s (Groq)', brand: true },
          ].map(s => (
            <div key={s.name} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ width: 80, fontSize: '0.82rem', fontWeight: s.brand ? 700 : 500, color: s.brand ? 'var(--brand)' : 'var(--text-secondary)' }}>{s.name}</span>
              <div style={{ flex: 1, height: 24, background: 'var(--border)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                <div style={{
                  width: `${s.speed}%`, height: '100%', borderRadius: 'var(--radius-full)',
                  background: s.brand ? 'linear-gradient(90deg, var(--brand), var(--agent-parse))' : 'var(--text-muted)',
                  transition: 'width 1s var(--ease)',
                }} />
              </div>
              <span style={{ width: 130, fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'right' }}>{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* PRICING */}
      <section className="landing-section" id="pricing">
        <h2 className="landing-section-title">Simple pricing</h2>
        <p className="landing-section-sub">Start free. Scale when you need to.</p>
        <div className="pricing-grid">
          {[
            { name: 'Starter', price: '$0', period: '/month', features: ['50 builds/month', '1 project', 'Basic memory', 'Community support'], cta: 'Start Free', featured: false },
            { name: 'Builder', price: '$20', period: '/month', features: ['Unlimited builds', 'Unlimited projects', 'Full memory + SIGMA-X', 'Priority support', 'Export to ZIP', 'Custom domains'], cta: 'Start Building', featured: true },
            { name: 'Studio', price: '$80', period: '/month', features: ['Everything in Builder', 'Shared team brain', '10 team seats', 'Enterprise deploy', 'API access', 'Dedicated support'], cta: 'Start Team Trial', featured: false },
          ].map(tier => (
            <div className={`pricing-card ${tier.featured ? 'featured' : ''}`} key={tier.name}>
              {tier.featured && (
                <div className="badge badge-brand" style={{ position: 'absolute', top: -10, right: 20 }}>Recommended</div>
              )}
              <div className="pricing-name">{tier.name}</div>
              <div className="pricing-price">{tier.price}<span>{tier.period}</span></div>
              <ul className="pricing-features">
                {tier.features.map(f => (
                  <li key={f}><CheckCircle2 size={14} style={{ color: 'var(--success)', flexShrink: 0 }} /> {f}</li>
                ))}
              </ul>
              <button className={`btn ${tier.featured ? 'btn-brand' : 'btn-secondary'}`} style={{ width: '100%' }} onClick={() => router.push('/build')}>
                {tier.cta} <ChevronRight size={14} />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="footer-links">
          <a href="#">About</a>
          <a href="#">Docs</a>
          <a href="#">GitHub</a>
          <a href="#">Twitter</a>
          <a href="#">Privacy</a>
        </div>
        <div className="footer-copy">
          © 2026 NEXUS-Ω · Open source core · Apache 2.0
        </div>
      </footer>
    </div>
  );
}
