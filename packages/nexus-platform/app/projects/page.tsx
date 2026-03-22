'use client';

import Sidebar from '@/components/Sidebar';
import { FolderOpen, Plus, Calendar, Shield, Search } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface Project {
  id: string;
  name: string;
  description: string;
  framework: string;
  updatedAt: string;
  securityScore: number;
}

export default function ProjectsPage() {
  const router = useRouter();
  const [projects] = useState<Project[]>([]);
  const [search, setSearch] = useState('');

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">Projects</span>
          </div>
          <div className="topbar-right">
            <div style={{ position: 'relative' }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input className="input" placeholder="Search projects..." style={{ paddingLeft: 30, width: 200 }}
                value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <button className="btn btn-brand btn-sm" onClick={() => router.push('/build')}>
              <Plus size={14} /> New Project
            </button>
          </div>
        </div>

        <div className="page-content">
          {projects.length === 0 ? (
            <div className="empty-state" style={{ minHeight: 400 }}>
              <div className="empty-state-icon"><FolderOpen size={24} /></div>
              <div className="empty-state-title">No projects yet</div>
              <div className="empty-state-text">Create your first project and let 6 AI agents build it for you.</div>
              <button className="btn btn-brand" style={{ marginTop: 16 }} onClick={() => router.push('/build')}>
                <Plus size={14} /> Start a new project
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
              {projects.filter(p => p.name.toLowerCase().includes(search.toLowerCase())).map(p => (
                <div className="card" key={p.id} style={{ cursor: 'pointer' }} onClick={() => router.push('/build')}>
                  <div className="card-header">
                    <h3 className="card-title">{p.name}</h3>
                    <div className="security-score">
                      <div className={`security-ring ${p.securityScore >= 90 ? 'high' : p.securityScore >= 70 ? 'medium' : 'low'}`}>
                        {p.securityScore}
                      </div>
                    </div>
                  </div>
                  <p className="feature-desc">{p.description}</p>
                  <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                    <span className="badge badge-gray">{p.framework}</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      <Calendar size={10} /> {p.updatedAt}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
