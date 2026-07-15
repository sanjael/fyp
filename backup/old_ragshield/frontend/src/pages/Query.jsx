import { useState, useRef } from 'react'
import { queryRAGShield } from '../api'

const RISK_COLORS = { low: 'var(--risk-low)', medium: 'var(--risk-medium)', high: 'var(--risk-high)' }
const RISK_BADGES = { low: 'badge-success', medium: 'badge-warning', high: 'badge-danger' }
const STRATEGY_INFO = {
  direct_generation: { icon: '✅', label: 'Direct Generation', color: 'var(--success)' },
  expand_retrieval: { icon: '🔄', label: 'Expanded Retrieval', color: 'var(--warning)' },
  verification_mode: { icon: '🔍', label: 'Verification Mode', color: 'var(--danger)' },
  blocked: { icon: '🚫', label: 'Blocked', color: 'var(--danger)' },
}

function RiskGauge({ score, level }) {
  const color = RISK_COLORS[level] || 'var(--text-muted)'
  const r = 54, cx = 70, cy = 70
  const circumference = Math.PI * r
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="risk-gauge-container">
      <svg width="140" height="80" viewBox="0 0 140 80">
        <defs>
          <linearGradient id="rg" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="50%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        {/* Track */}
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none" stroke="var(--border-medium)" strokeWidth="10" strokeLinecap="round" />
        {/* Fill */}
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={`${circumference * (score / 100)} ${circumference}`}
          style={{ transition: 'stroke-dasharray 1s ease, stroke 0.5s ease' }} />
        {/* Score text */}
        <text x={cx} y={cy - 8} textAnchor="middle" fill={color}
          fontSize="22" fontWeight="900" fontFamily="Inter, sans-serif">{Math.round(score)}%</text>
        <text x={cx} y={cy + 8} textAnchor="middle" fill="var(--text-muted)"
          fontSize="9" fontFamily="Inter, sans-serif" letterSpacing="1">RISK SCORE</text>
      </svg>
      <div className={`risk-level-label ${level}`} style={{ fontSize: '0.85rem', marginTop: -8 }}>
        {level?.toUpperCase()} RISK
      </div>
    </div>
  )
}

function CQSBar({ label, value, color }) {
  const pct = Math.min(100, Math.max(0, value))
  const barColor = pct >= 75 ? 'success' : pct >= 60 ? 'warning' : 'danger'
  return (
    <div style={{ marginBottom: '0.6rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{label}</span>
        <span style={{ fontSize: '0.78rem', fontWeight: 700, color }}>{pct.toFixed(1)}</span>
      </div>
      <div className="progress-bar-container">
        <div className={`progress-bar-fill ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function ChunkCard({ chunk, index, passed = true }) {
  const [expanded, setExpanded] = useState(false)
  const cqs = chunk.cqs_score || 0
  const verdict = chunk.shield_verdict || (passed ? 'passed' : 'filtered')

  return (
    <div className={`chunk-card ${verdict.includes('filter') ? 'filtered' : verdict.includes('flag') ? 'flagged' : 'passed'}`}>
      <div className="chunk-header">
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flex: 1, minWidth: 0 }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>Chunk {index + 1}</span>
          <span className="chunk-source">{chunk.source}</span>
          {chunk.year && <span className="badge badge-info" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>📅 {chunk.year}</span>}
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexShrink: 0 }}>
          {cqs > 0 && (
            <span style={{
              fontSize: '0.78rem', fontWeight: 800, padding: '0.15rem 0.5rem',
              borderRadius: 6, background: cqs >= 75 ? 'rgba(16,185,129,0.15)' : cqs >= 60 ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
              color: cqs >= 75 ? 'var(--success)' : cqs >= 60 ? 'var(--warning)' : 'var(--danger)'
            }}>CQS {cqs.toFixed(1)}</span>
          )}
          <span style={{
            fontSize: '0.7rem', fontWeight: 700, padding: '0.1rem 0.5rem',
            borderRadius: 6, background: chunk.similarity_score >= 0.8 ? 'rgba(6,182,212,0.15)' : 'var(--border-subtle)',
            color: chunk.similarity_score >= 0.8 ? 'var(--info)' : 'var(--text-muted)'
          }}>{(chunk.similarity_score * 100).toFixed(0)}%</span>
          <button onClick={() => setExpanded(e => !e)}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.85rem' }}>
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      <p className="chunk-text">{expanded ? chunk.text : (chunk.text || '').slice(0, 200) + (chunk.text?.length > 200 ? '...' : '')}</p>

      {!passed && chunk.filter_reason && (
        <div style={{ marginTop: '0.5rem', padding: '0.4rem 0.75rem', background: 'rgba(239,68,68,0.08)', borderRadius: 6, fontSize: '0.78rem', color: 'var(--danger)' }}>
          🚫 {chunk.filter_reason}
        </div>
      )}

      {expanded && chunk.component_scores && (
        <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 8 }}>
          <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>CQS Components</div>
          <CQSBar label="Relevance" value={chunk.component_scores.relevance} color="var(--brand-primary)" />
          <CQSBar label="Credibility" value={chunk.component_scores.credibility} color="var(--info)" />
          <CQSBar label="Consistency" value={chunk.component_scores.consistency} color="var(--success)" />
          <CQSBar label="Freshness" value={chunk.component_scores.freshness} color="var(--warning)" />
        </div>
      )}
    </div>
  )
}

const SUGGESTED = [
  'What is machine learning?',
  'Explain neural networks in simple terms',
  'What are the limitations of deep learning?',
  'How does retrieval augmented generation work?',
  'What is the difference between supervised and unsupervised learning?',
]

export default function Query() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('answer')
  const textareaRef = useRef(null)

  const handleQuery = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setActiveTab('answer')

    try {
      const res = await queryRAGShield({ query: query.trim(), enable_adaptive: true })
      setResult(res.data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Query failed. Make sure the backend is running and documents are uploaded.')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleQuery()
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">💬 Query RAGShield</h1>
        <p className="page-subtitle">Ask questions about your indexed documents. RAGShield validates context before generating answers.</p>
      </div>

      {/* Query Input */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="query-input-wrapper">
          <textarea
            ref={textareaRef}
            className="query-textarea"
            placeholder="Ask a question about your documents... (Ctrl+Enter to submit)"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={3}
          />
          <button
            className="btn btn-primary btn-lg"
            onClick={handleQuery}
            disabled={loading || !query.trim()}
            style={{ flexShrink: 0, alignSelf: 'stretch', borderRadius: 12, minWidth: 100 }}
          >
            {loading ? <span className="spinner" /> : <><span>🔍</span><span>Search</span></>}
          </button>
        </div>

        {/* Suggested Queries */}
        <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {SUGGESTED.map((s, i) => (
            <button key={i}
              onClick={() => { setQuery(s); setTimeout(() => textareaRef.current?.focus(), 0) }}
              style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
                borderRadius: 20, padding: '0.25rem 0.75rem', fontSize: '0.78rem',
                color: 'var(--text-secondary)', cursor: 'pointer', transition: 'all 0.15s',
                fontFamily: 'inherit'
              }}
              className="hover-effect"
            >{s}</button>
          ))}
        </div>
      </div>

      {error && (
        <div style={{
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 12, padding: '1rem 1.25rem', marginBottom: '1.5rem',
          color: 'var(--danger)', fontSize: '0.9rem', display: 'flex', gap: '0.5rem'
        }}>
          <span>❌</span><span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="card loading-overlay" style={{ marginBottom: '1.5rem' }}>
          <div style={{ position: 'relative' }}>
            <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
          </div>
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontWeight: 700, color: 'var(--text-primary)' }}>RAGShield Processing...</p>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Retrieving → Shielding → Scoring → Risk Analysis → Generating</p>
          </div>
        </div>
      )}

      {result && (
        <div className="scale-in">
          {/* Summary Stats */}
          <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
            <div className="stat-card">
              <div className="stat-icon brand">🔍</div>
              <div>
                <div className="stat-value">{result.retrieved_count}</div>
                <div className="stat-label">Retrieved</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon success">✅</div>
              <div>
                <div className="stat-value">{result.passed_count}</div>
                <div className="stat-label">Passed Shield</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon warning">🚫</div>
              <div>
                <div className="stat-value">{result.filtered_count}</div>
                <div className="stat-label">Filtered</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon info">⏱️</div>
              <div>
                <div className="stat-value" style={{ fontSize: '1.2rem' }}>{result.processing_time_seconds}s</div>
                <div className="stat-label">Processing Time</div>
              </div>
            </div>
          </div>

          {/* Risk + Strategy Banner */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem'
          }}>
            <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              <RiskGauge score={result.risk?.risk_score || 0} level={result.risk?.risk_level || 'low'} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Hallucination Risk</div>
                {result.risk?.risk_factors?.map((f, i) => (
                  <div key={i} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.2rem', display: 'flex', gap: '0.35rem', alignItems: 'flex-start' }}>
                    <span>{f.severity === 'critical' ? '🔴' : f.severity === 'high' ? '🟠' : f.severity === 'medium' ? '🟡' : '🟢'}</span>
                    <span>{f.factor}: {f.detail}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>Generation Strategy</div>
              {(() => {
                const si = STRATEGY_INFO[result.strategy] || STRATEGY_INFO.direct_generation
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div style={{ fontSize: '2rem' }}>{si.icon}</div>
                    <div style={{ fontWeight: 700, color: si.color }}>{si.label}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {result.risk?.recommendation?.description}
                    </div>
                    {result.cqs_stats && (
                      <div style={{ marginTop: '0.5rem' }}>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                          <div><span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--brand-primary)' }}>{result.cqs_stats.avg_cqs?.toFixed(1)}</span><div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Avg CQS</div></div>
                          <div><span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--info)' }}>{result.cqs_stats.overall_quality_level}</span><div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Quality</div></div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}
            </div>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1rem', background: 'var(--bg-secondary)', borderRadius: 10, padding: '0.25rem', border: '1px solid var(--border-subtle)', width: 'fit-content' }}>
            {[
              { id: 'answer', label: '💬 Answer' },
              { id: 'context', label: `✅ Passed (${result.passed_count})` },
              { id: 'filtered', label: `🚫 Filtered (${result.filtered_count})` },
              { id: 'sources', label: '📚 Sources' },
            ].map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '0.5rem 1rem', borderRadius: 8, border: 'none', cursor: 'pointer',
                  fontFamily: 'inherit', fontWeight: 600, fontSize: '0.85rem', transition: 'all 0.15s',
                  background: activeTab === tab.id ? 'var(--brand-primary)' : 'transparent',
                  color: activeTab === tab.id ? 'white' : 'var(--text-secondary)',
                  boxShadow: activeTab === tab.id ? 'var(--shadow-md)' : 'none',
                }}>{tab.label}</button>
            ))}
          </div>

          {/* Answer Tab */}
          {activeTab === 'answer' && (
            <div className="card fade-in">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--gradient-brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem' }}>🤖</div>
                <div>
                  <div style={{ fontWeight: 700 }}>RAGShield Answer</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Confidence: <span style={{ color: result.confidence === 'high' ? 'var(--success)' : result.confidence === 'medium' ? 'var(--warning)' : 'var(--danger)', fontWeight: 700 }}>{result.confidence?.toUpperCase()}</span>
                  </div>
                </div>
                <span className={`badge ${RISK_BADGES[result.risk?.risk_level]}`} style={{ marginLeft: 'auto' }}>{result.risk?.risk_level} risk</span>
              </div>
              <div style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
                borderRadius: 10, padding: '1.25rem', lineHeight: 1.8,
                fontSize: '0.95rem', whiteSpace: 'pre-wrap', color: 'var(--text-primary)'
              }}>
                {result.answer}
              </div>
            </div>
          )}

          {/* Passed Chunks Tab */}
          {activeTab === 'context' && (
            <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {result.scored_chunks?.length === 0
                ? <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No chunks passed the shield</div>
                : result.scored_chunks?.map((chunk, i) => <ChunkCard key={i} chunk={chunk} index={i} passed />)
              }
            </div>
          )}

          {/* Filtered Chunks Tab */}
          {activeTab === 'filtered' && (
            <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {result.filtered_chunks?.length === 0
                ? <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No chunks were filtered</div>
                : result.filtered_chunks?.map((chunk, i) => <ChunkCard key={i} chunk={chunk} index={i} passed={false} />)
              }
            </div>
          )}

          {/* Sources Tab */}
          {activeTab === 'sources' && (
            <div className="fade-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
              {result.sources?.map((s, i) => (
                <div key={i} className="card" style={{ padding: '1rem' }}>
                  <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>📄</div>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: '0.3rem', wordBreak: 'break-word' }}>{s.title || s.filename}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <div>📅 {s.year || 'Unknown'}</div>
                    <div className="font-mono" style={{ marginTop: 2, fontSize: '0.7rem' }}>{s.filename}</div>
                    {s.cqs_score && <div style={{ marginTop: 4, color: 'var(--brand-primary)' }}>CQS: {s.cqs_score.toFixed(1)}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
