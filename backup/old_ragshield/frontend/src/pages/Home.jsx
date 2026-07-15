import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getStats } from '../api'

const PIPELINE_STEPS = [
  { icon: '📄', label: 'Upload PDF' },
  { icon: '✂️', label: 'Chunking' },
  { icon: '🔢', label: 'Embedding' },
  { icon: '🗄️', label: 'Vector DB' },
  { icon: '🔍', label: 'Retriever' },
  { icon: '🛡️', label: 'Shield' },
  { icon: '📊', label: 'CQS Score' },
  { icon: '⚡', label: 'Risk Engine' },
  { icon: '🔄', label: 'Adaptive' },
  { icon: '🤖', label: 'LLM' },
]

const FEATURES = [
  {
    icon: '🛡️',
    title: 'Context Shield Layer',
    desc: 'Pre-generation validation that filters duplicate, noisy, and irrelevant chunks before they reach the LLM.',
    badge: 'Core Innovation',
    badgeClass: 'badge-primary',
  },
  {
    icon: '⚡',
    title: 'Risk Prediction Engine',
    desc: 'Predicts hallucination probability using CQS, similarity scores, contradiction count, and source reliability.',
    badge: 'Research Novelty',
    badgeClass: 'badge-warning',
  },
  {
    icon: '🔄',
    title: 'Adaptive Generation',
    desc: 'Dynamically switches strategy: Direct → Expand Retrieval → Verification Mode based on risk level.',
    badge: 'Self-Adaptive',
    badgeClass: 'badge-success',
  },
  {
    icon: '💉',
    title: 'Poisoning Simulator',
    desc: 'Injects adversarial documents to benchmark RAGShield robustness against noisy retrieval environments.',
    badge: 'Phase 2',
    badgeClass: 'badge-danger',
  },
  {
    icon: '📊',
    title: 'Explainability Dashboard',
    desc: 'Full visibility into retrieved chunks, CQS scores, risk factors, and shield decisions.',
    badge: 'Transparency',
    badgeClass: 'badge-info',
  },
  {
    icon: '📈',
    title: 'CQS Scoring',
    desc: 'Each chunk scored: 0.4×Relevance + 0.3×Credibility + 0.2×Consistency + 0.1×Freshness',
    badge: 'Quality Metrics',
    badgeClass: 'badge-primary',
  },
]

export default function Home({ health }) {
  const [stats, setStats] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    getStats().then(r => setStats(r.data)).catch(() => {})
  }, [])

  const isOnline = health?.status === 'healthy'

  return (
    <div className="fade-in">
      {/* Hero */}
      <div style={{ marginBottom: '3rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{
            width: 64, height: 64, borderRadius: 16,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '2rem', boxShadow: 'var(--shadow-brand)'
          }}>🛡️</div>
          <div>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 900, letterSpacing: '-0.04em' }}>
              <span style={{ background: 'linear-gradient(135deg, #818cf8, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>RAG</span>Shield
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: 2 }}>
              Risk-Aware &amp; Self-Adaptive Hallucination Prevention
            </p>
          </div>
        </div>

        <p style={{ fontSize: '1.05rem', color: 'var(--text-secondary)', maxWidth: 640, lineHeight: 1.8, marginBottom: '2rem' }}>
          A research-grade framework that <strong style={{ color: 'var(--text-primary)' }}>prevents hallucinations before generation</strong> by evaluating context quality, predicting risk, and adaptively controlling the generation pipeline.
        </p>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button className="btn btn-primary btn-lg" onClick={() => navigate('/upload')}>
            <span>📄</span> Upload Documents
          </button>
          <button className="btn btn-secondary btn-lg" onClick={() => navigate('/query')}>
            <span>💬</span> Start Querying
          </button>
        </div>
      </div>

      {/* System Status */}
      <div className="stats-grid animate-stagger" style={{ marginBottom: '2rem' }}>
        <div className="stat-card">
          <div className={`stat-icon ${isOnline ? 'success' : 'warning'}`}>{isOnline ? '✅' : '⚠️'}</div>
          <div>
            <div className="stat-value" style={{ color: isOnline ? 'var(--success)' : 'var(--warning)', fontSize: '1.2rem', fontWeight: 700 }}>
              {isOnline ? 'Online' : 'Offline'}
            </div>
            <div className="stat-label">Backend Status</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon brand">📚</div>
          <div>
            <div className="stat-value">{health?.total_chunks || 0}</div>
            <div className="stat-label">Indexed Chunks</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon info">🤖</div>
          <div>
            <div className="stat-value" style={{ fontSize: '0.9rem', fontWeight: 700 }}>
              {health?.llm_available ? 'Gemini' : 'Demo'}
            </div>
            <div className="stat-label">LLM Mode</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon success">🔢</div>
          <div>
            <div className="stat-value" style={{ fontSize: '0.75rem', fontWeight: 700 }}>BGE-small</div>
            <div className="stat-label">Embedding Model</div>
          </div>
        </div>
      </div>

      {/* Pipeline Visualization */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <div className="card-title">RAGShield Pipeline</div>
          <span className="badge badge-primary">10 Stages</span>
        </div>
        <div className="pipeline-steps">
          {PIPELINE_STEPS.map((step, i) => (
            <div key={i} className="pipeline-step">
              <div className={`pipeline-node ${isOnline ? (i < 6 ? 'success' : 'brand') : 'pending'} ${isOnline ? 'active' : ''}`}>
                {step.icon}
              </div>
              <div className="pipeline-label">{step.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Features Grid */}
      <div style={{ marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.4rem', marginBottom: '1.25rem', fontWeight: 700 }}>Core Features</h2>
        <div className="grid-3 animate-stagger" style={{ gap: '1rem' }}>
          {FEATURES.map((f, i) => (
            <div key={i} className="card" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '1.8rem' }}>{f.icon}</span>
                <span className={`badge ${f.badgeClass}`}>{f.badge}</span>
              </div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.4rem' }}>{f.title}</h3>
              <p style={{ fontSize: '0.82rem', lineHeight: 1.6, color: 'var(--text-muted)' }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Research Novelties */}
      <div className="card" style={{ marginTop: '2rem', background: 'rgba(99,102,241,0.05)', borderColor: 'rgba(99,102,241,0.2)' }}>
        <div className="card-header">
          <div className="card-title">Research Novelties</div>
          <span className="badge badge-primary">IEEE-Level</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
          {[
            { n: '01', title: 'Pre-Generation Prevention', sub: 'Detect hallucination risk before LLM generation' },
            { n: '02', title: 'Hallucination Risk Score', sub: 'Quantify risk as 0–100% probability score' },
            { n: '03', title: 'Self-Adaptive Pipeline', sub: 'Strategy changes based on context quality' },
            { n: '04', title: 'Poisoning Resistance', sub: 'Robust to adversarial noisy retrievals' },
            { n: '05', title: 'Context Shield Layer', sub: 'Dedicated protection between Retriever & LLM' },
          ].map((n, i) => (
            <div key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <div style={{
                width: 36, height: 36, borderRadius: 8, background: 'rgba(99,102,241,0.15)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.75rem', fontWeight: 800, color: 'var(--brand-primary)', flexShrink: 0,
                fontFamily: 'JetBrains Mono, monospace'
              }}>{n.n}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: 2 }}>{n.title}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{n.sub}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
