import React, { useEffect, useState } from 'react';
import { Database, FileText, Activity, Clock } from 'lucide-react';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState({
    documents: 0,
    chunks: 0,
    avgTRRI: 0,
    activeExperiments: 0
  });

  useEffect(() => {
    axios.get('/api/v1/stats/overview')
      .then(res => setStats(res.data))
      .catch(err => console.error("Error fetching stats", err));
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Platform Overview</h1>
        <p style={{ color: 'var(--text-muted)' }}>Welcome to your RAGGuard-TR temporal-aware metrics dashboard.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        
        {/* Stat Card 1 */}
        <div className="glass-panel" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: '-20px', right: '-20px', opacity: 0.1 }}>
            <FileText size={120} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <div style={{ padding: '12px', background: 'rgba(0, 240, 255, 0.1)', borderRadius: '12px', color: 'var(--primary)' }}>
              <FileText size={24} />
            </div>
            <h3 style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Total Documents</h3>
          </div>
          <div style={{ fontSize: '3rem', fontWeight: 700, fontFamily: 'var(--font-heading)' }}>
            {stats.documents}
          </div>
          <div style={{ color: 'var(--accent-green)', fontSize: '0.85rem', marginTop: '8px', fontWeight: 600 }}>
            +3 this week
          </div>
        </div>

        {/* Stat Card 2 */}
        <div className="glass-panel" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: '-20px', right: '-20px', opacity: 0.1 }}>
            <Database size={120} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <div style={{ padding: '12px', background: 'rgba(112, 0, 255, 0.1)', borderRadius: '12px', color: 'var(--secondary)' }}>
              <Database size={24} />
            </div>
            <h3 style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Vector Chunks</h3>
          </div>
          <div style={{ fontSize: '3rem', fontWeight: 700, fontFamily: 'var(--font-heading)' }}>
            {stats.chunks}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px' }}>
            Indexed in ChromaDB
          </div>
        </div>

        {/* Stat Card 3 */}
        <div className="glass-panel" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: '-20px', right: '-20px', opacity: 0.1 }}>
            <Activity size={120} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <div style={{ padding: '12px', background: 'rgba(0, 230, 118, 0.1)', borderRadius: '12px', color: 'var(--accent-green)' }}>
              <Activity size={24} />
            </div>
            <h3 style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Avg TRRI Score</h3>
          </div>
          <div style={{ fontSize: '3rem', fontWeight: 700, fontFamily: 'var(--font-heading)' }}>
            {stats.avgTRRI}
          </div>
          <div style={{ color: 'var(--accent-green)', fontSize: '0.85rem', marginTop: '8px', fontWeight: 600 }}>
            Highly Reliable
          </div>
        </div>

        {/* Stat Card 4 */}
        <div className="glass-panel" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: '-20px', right: '-20px', opacity: 0.1 }}>
            <Clock size={120} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <div style={{ padding: '12px', background: 'rgba(255, 234, 0, 0.1)', borderRadius: '12px', color: 'var(--accent-yellow)' }}>
              <Clock size={24} />
            </div>
            <h3 style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Active Experiments</h3>
          </div>
          <div style={{ fontSize: '3rem', fontWeight: 700, fontFamily: 'var(--font-heading)' }}>
            {stats.activeExperiments}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px' }}>
            Celery workers running
          </div>
        </div>

      </div>

      <div className="glass-panel" style={{ padding: '32px' }}>
        <h2 style={{ marginBottom: '24px', fontSize: '1.5rem' }}>System Architecture</h2>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '200px', padding: '20px', background: 'rgba(0,0,0,0.3)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ color: 'var(--primary)', marginBottom: '8px' }}>Language Model</h4>
            <p>Ollama (llama3.1:8b)</p>
          </div>
          <div style={{ flex: 1, minWidth: '200px', padding: '20px', background: 'rgba(0,0,0,0.3)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ color: 'var(--secondary)', marginBottom: '8px' }}>Embedding Engine</h4>
            <p>nomic-embed-text</p>
          </div>
          <div style={{ flex: 1, minWidth: '200px', padding: '20px', background: 'rgba(0,0,0,0.3)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ color: 'var(--accent-green)', marginBottom: '8px' }}>Relational Data</h4>
            <p>PostgreSQL 15</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
