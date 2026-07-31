import React, { useEffect, useState } from 'react';
import { Database, FileText, Activity, Clock, ShieldCheck, HelpCircle } from 'lucide-react';
import axios from 'axios';

const FEATURE_LABELS: Record<string, string> = {
  temporal_freshness:    'Temporal Freshness',
  temporal_availability: 'Temporal Availability',
  source_credibility:    'Source Credibility',
  evidence_consistency:  'Evidence Consistency',
  evidence_sufficiency:  'Evidence Sufficiency',
};

const ScoreBar = ({ score, label }: { score: number | null; label: string }) => {
  if (score === null || score === undefined) {
    return (
      <div style={{ marginBottom: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{label}</span>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>N/A</span>
        </div>
        <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }} />
      </div>
    );
  }

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

interface OverviewStats {
  documents: number;
  chunks: number;
  avgTRRI: number;
  activeExperiments: number;
  latest_rrfe?: Record<string, number | null> | null;
  has_executed_query?: boolean;
}

const Dashboard = () => {
  const [stats, setStats] = useState<OverviewStats>({
    documents: 0,
    chunks: 0,
    avgTRRI: 0,
    activeExperiments: 0,
    latest_rrfe: null,
    has_executed_query: false,
  });

  const fetchStats = () => {
    axios.get('/api/v1/stats/overview')
      .then(res => setStats(res.data))
      .catch(err => console.error('Error fetching stats', err));
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000); // Live poll stats every 3s
    return () => clearInterval(interval);
  }, []);

  const featureKeys = [
    'temporal_freshness',
    'temporal_availability',
    'source_credibility',
    'evidence_consistency',
    'evidence_sufficiency',
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
          { icon: <Activity size={24} />, label: 'Avg TRRI Score',     value: stats.avgTRRI > 0 ? `${(stats.avgTRRI * 100).toFixed(1)}%` : 'N/A', color: 'var(--accent-green)', bg: 'rgba(0,230,118,0.1)' },
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

      {/* TRRI Feature Breakdown & System Architecture */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        <div className="glass-panel" style={{ padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
            <ShieldCheck size={20} color="var(--primary)" />
            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>TRRI Feature Breakdown</h2>
          </div>

          {!stats.has_executed_query || !stats.latest_rrfe ? (
            <div style={{ padding: '32px 20px', textAlign: 'center', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', border: '1px border-color' }}>
              <HelpCircle size={36} color="var(--text-muted)" style={{ marginBottom: '12px', opacity: 0.6 }} />
              <p style={{ color: 'var(--text-primary)', fontWeight: 600, margin: 0, fontSize: '1rem' }}>
                No query executed yet.
              </p>
              <p style={{ color: 'var(--text-muted)', margin: '8px 0 0', fontSize: '0.82rem', lineHeight: 1.5 }}>
                Execute a query in the Chat interface to evaluate live temporal recency, credibility, consistency, and sufficiency feature scores.
              </p>
            </div>
          ) : (
            <>
              {featureKeys.map((key) => (
                <ScoreBar
                  key={key}
                  score={stats.latest_rrfe ? stats.latest_rrfe[key] ?? null : null}
                  label={FEATURE_LABELS[key]}
                />
              ))}
              <p style={{ margin: '16px 0 0', fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Displaying RRFE scores extracted from the latest query execution.
              </p>
            </>
          )}
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
