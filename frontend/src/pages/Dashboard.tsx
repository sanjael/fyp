import React, { useEffect, useState } from 'react';
import { Database, FileText, Activity, Clock, ShieldCheck } from 'lucide-react';
import axios from 'axios';

const FEATURE_LABELS: Record<string, string> = {
  temporal_freshness:    'Temporal Freshness',
  temporal_availability: 'Temporal Availability',
  source_credibility:    'Source Credibility',
  evidence_consistency:  'Evidence Consistency',
  evidence_sufficiency:  'Evidence Sufficiency',
};

const ScoreBar = ({ score, label }: { score: number; label: string }) => {
  const pct = Math.round(score * 100);
  const color = score >= 0.7 ? 'var(--accent-green)' : score >= 0.45 ? 'var(--accent-yellow)' : 'var(--accent-red)';
  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{label}</span>
        <span style={{ fontSize: '0.85rem', fontWeight: 700, color }}>{pct}%</span>
      </div>
      <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: '3px', transition: 'width 0.5s ease' }} />
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [stats, setStats] = useState({ documents: 0, chunks: 0, avgTRRI: 0, activeExperiments: 0 });

  useEffect(() => {
    axios.get('/api/v1/stats/overview')
      .then(res => setStats(res.data))
      .catch(err => console.error('Error fetching stats', err));
  }, []);

  // Placeholder feature scores shown until a real query populates them
  const placeholderFeatures = [
    { key: 'temporal_freshness',    score: 0 },
    { key: 'temporal_availability', score: 0 },
    { key: 'source_credibility',    score: 0 },
    { key: 'evidence_consistency',  score: 0 },
    { key: 'evidence_sufficiency',  score: 0 },
  ];

  return (
    <div>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Platform Overview</h1>
        <p style={{ color: 'var(--text-muted)' }}>RAGGuard-TR — Temporal-Aware Reliability and Risk Index dashboard.</p>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        {[
          { icon: <FileText size={24} />, label: 'Total Documents',    value: stats.documents,         color: 'var(--primary)',      bg: 'rgba(0,240,255,0.1)' },
          { icon: <Database size={24} />, label: 'Vector Chunks',      value: stats.chunks,            color: 'var(--secondary)',    bg: 'rgba(112,0,255,0.1)' },
          { icon: <Activity size={24} />, label: 'Avg TRRI Score',     value: `${(stats.avgTRRI * 100).toFixed(1)}%`, color: 'var(--accent-green)', bg: 'rgba(0,230,118,0.1)' },
          { icon: <Clock size={24} />,    label: 'Active Experiments', value: stats.activeExperiments, color: 'var(--accent-yellow)', bg: 'rgba(255,234,0,0.1)' },
        ].map(({ icon, label, value, color, bg }) => (
          <div key={label} className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
              <div style={{ padding: '12px', background: bg, borderRadius: '12px', color }}>{icon}</div>
              <h3 style={{ color: 'var(--text-muted)', fontSize: '1rem', margin: 0 }}>{label}</h3>
            </div>
            <div style={{ fontSize: '2.6rem', fontWeight: 700 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* TRRI Feature Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        <div className="glass-panel" style={{ padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
            <ShieldCheck size={20} color="var(--primary)" />
            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>TRRI Feature Breakdown</h2>
          </div>
          {placeholderFeatures.map(({ key, score }) => (
            <ScoreBar key={key} score={score} label={FEATURE_LABELS[key]} />
          ))}
          <p style={{ margin: '16px 0 0', fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            Scores update after each query in the Query Engine.
          </p>
        </div>

        {/* System Architecture */}
        <div className="glass-panel" style={{ padding: '28px' }}>
          <h2 style={{ marginBottom: '20px', fontSize: '1.2rem' }}>System Architecture</h2>
          {[
            { label: 'Language Model',   value: 'Ollama (qwen2.5)',      color: 'var(--primary)' },
            { label: 'Embedding Engine', value: 'nomic-embed-text',      color: 'var(--secondary)' },
            { label: 'Vector Store',     value: 'ChromaDB (persistent)', color: 'var(--accent-green)' },
            { label: 'Relational DB',    value: 'PostgreSQL 15',         color: 'var(--accent-yellow)' },
            { label: 'TRRI Predictor',   value: 'XGBoost Regressor',     color: 'var(--primary)' },
            { label: 'RRFE Features',    value: '5 dimensions',          color: 'var(--accent-green)' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{label}</span>
              <span style={{ color, fontWeight: 600, fontSize: '0.9rem' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;


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
