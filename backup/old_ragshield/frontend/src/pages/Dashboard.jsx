import { useState, useEffect, useCallback } from 'react'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import { getStats, listDocuments, runPoisonTest } from '../api'

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6']

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-medium)', borderRadius: 8, padding: '0.6rem 1rem', fontSize: '0.82rem' }}>
        <p style={{ color: '#94a3b8', marginBottom: 4 }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color || '#6366f1', fontWeight: 700 }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</p>
        ))}
      </div>
    )
  }
  return null
}

function StatCard({ icon, title, value, sub, colorClass }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${colorClass}`}>{icon}</div>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{title}</div>
        {sub && <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>{sub}</div>}
      </div>
    </div>
  )
}

function SectionTitle({ children }) {
  return <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>{children}</h2>
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [documents, setDocuments] = useState([])
  const [poisonQuery, setPoisonQuery] = useState('What is machine learning?')
  const [poisonRatio, setPoisonRatio] = useState(0.3)
  const [poisonResult, setPoisonResult] = useState(null)
  const [poisonLoading, setPoisonLoading] = useState(false)
  const [loading, setLoading] = useState(true)

  const fetchAll = useCallback(() => {
    setLoading(true)
    Promise.all([getStats(), listDocuments()])
      .then(([s, d]) => { setStats(s.data); setDocuments(d.data.documents || []) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { fetchAll() }, [fetchAll])

  const runPoison = async () => {
    setPoisonLoading(true)
    setPoisonResult(null)
    try {
      const res = await runPoisonTest({ query: poisonQuery, poison_ratio: poisonRatio })
      setPoisonResult(res.data)
    } catch (err) {
      setPoisonResult({ error: err?.response?.data?.detail || 'Test failed' })
    } finally {
      setPoisonLoading(false)
    }
  }

  if (loading) {
    return <div className="loading-overlay"><div className="spinner" style={{ width: 40, height: 40 }} /><p>Loading Dashboard...</p></div>
  }

  // Radar chart data for CQS weights
  const cqsRadarData = stats ? [
    { subject: 'Relevance', value: (stats.cqs_weights?.relevance || 0.4) * 100, fullMark: 100 },
    { subject: 'Credibility', value: (stats.cqs_weights?.credibility || 0.3) * 100, fullMark: 100 },
    { subject: 'Consistency', value: (stats.cqs_weights?.consistency || 0.2) * 100, fullMark: 100 },
    { subject: 'Freshness', value: (stats.cqs_weights?.freshness || 0.1) * 100, fullMark: 100 },
  ] : []

  // Document source types
  const sourceTypeCounts = documents.reduce((acc, d) => {
    const t = d.source_type || 'unknown'
    acc[t] = (acc[t] || 0) + 1
    return acc
  }, {})
  const pieData = Object.entries(sourceTypeCounts).map(([name, value]) => ({ name: name.replace('_', ' '), value }))

  // Document chunk bar data
  const barData = documents.slice(0, 8).map(d => ({
    name: (d.filename || '').replace('.pdf', '').slice(0, 15),
    chunks: d.chunk_count || 0,
  }))

  // Risk thresholds
  const riskBarData = [
    { name: 'Low Risk', threshold: stats?.risk_thresholds?.low || 30, color: '#10b981' },
    { name: 'High Risk', threshold: stats?.risk_thresholds?.high || 60, color: '#ef4444' },
  ]

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">📊 Explainability Dashboard</h1>
        <p className="page-subtitle">System metrics, shield configuration, and research benchmarks</p>
      </div>

      {/* System Stats */}
      <div className="stats-grid animate-stagger" style={{ marginBottom: '2rem' }}>
        <StatCard icon="📚" title="Total Documents" value={documents.length} colorClass="brand" />
        <StatCard icon="🗂️" title="Total Chunks" value={stats?.total_chunks || 0} colorClass="info" />
        <StatCard icon="🤖" title="LLM Status" value={stats?.llm_available ? 'Active' : 'Demo'} sub={stats?.llm_model} colorClass={stats?.llm_available ? 'success' : 'warning'} />
        <StatCard icon="🔢" title="Embedding Dim" value="384" sub={stats?.embedding_model?.split('/')[1]} colorClass="brand" />
      </div>

      <div className="grid-2" style={{ gap: '1.5rem', marginBottom: '2rem' }}>
        {/* CQS Weights Radar */}
        <div className="card">
          <SectionTitle>⚖️ CQS Weight Configuration</SectionTitle>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={cqsRadarData}>
              <PolarGrid stroke="var(--border-medium)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Radar name="Weight" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
              <Tooltip content={<CustomTooltip />} />
            </RadarChart>
          </ResponsiveContainer>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' }}>
            {stats?.cqs_weights && Object.entries(stats.cqs_weights).map(([k, v], i) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', padding: '0.25rem 0.5rem', background: 'var(--bg-secondary)', borderRadius: 6 }}>
                <span style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>{k}</span>
                <span style={{ fontWeight: 700, color: COLORS[i] }}>{(v * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Document Sources Pie */}
        <div className="card">
          <SectionTitle>📄 Document Source Types</SectionTitle>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`} labelLine={false} fontSize={11}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              No documents indexed yet
            </div>
          )}
        </div>
      </div>

      {/* Chunk Distribution */}
      {barData.length > 0 && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <SectionTitle>🗂️ Chunks per Document</SectionTitle>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} margin={{ top: 5, right: 20, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-25} textAnchor="end" />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="chunks" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Shield Configuration */}
      <div className="grid-2" style={{ gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card">
          <SectionTitle>🛡️ Shield Thresholds</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              { label: 'Relevance Threshold', value: (stats?.shield_thresholds?.relevance || 0.65) * 100, unit: '%', desc: 'Min similarity to pass' },
              { label: 'Duplicate Threshold', value: (stats?.shield_thresholds?.duplicate || 0.95) * 100, unit: '%', desc: 'Max similarity before dedup' },
              { label: 'Risk: Low Ceiling', value: stats?.risk_thresholds?.low || 30, unit: '%', desc: 'Below = direct generation' },
              { label: 'Risk: High Floor', value: stats?.risk_thresholds?.high || 60, unit: '%', desc: 'Above = verification mode' },
            ].map((item, i) => (
              <div key={i} style={{ padding: '0.6rem 0.75rem', background: 'var(--bg-secondary)', borderRadius: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{item.label}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{item.desc}</div>
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: COLORS[i] }}>{item.value}{item.unit}</div>
                </div>
                <div className="progress-bar-container">
                  <div className="progress-bar-fill brand" style={{ width: `${item.value}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Levels Guide */}
        <div className="card">
          <SectionTitle>⚡ Adaptive Strategy Guide</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              { level: 'LOW', range: '0–30%', color: 'var(--risk-low)', action: 'Direct Generation', desc: 'High quality context. Answer immediately.', icon: '✅' },
              { level: 'MEDIUM', range: '30–60%', color: 'var(--risk-medium)', action: 'Expand Retrieval', desc: 'Fetch 2× more chunks, re-evaluate.', icon: '🔄' },
              { level: 'HIGH', range: '60–100%', color: 'var(--risk-high)', action: 'Verification Mode', desc: 'Re-retrieve, cross-verify, strict filter.', icon: '🔍' },
            ].map((r, i) => (
              <div key={i} style={{ border: `1px solid ${r.color}33`, borderRadius: 10, padding: '0.75rem 1rem', background: `${r.color}08` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontSize: '1.5rem' }}>{r.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.2rem' }}>
                      <span style={{ fontWeight: 800, color: r.color, fontSize: '0.85rem' }}>{r.level}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({r.range})</span>
                      <span className="badge" style={{ fontSize: '0.65rem', background: `${r.color}15`, color: r.color, border: `1px solid ${r.color}30` }}>{r.action}</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{r.desc}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Context Poisoning Simulator */}
      <div className="card" style={{ background: 'rgba(239,68,68,0.04)', borderColor: 'rgba(239,68,68,0.2)' }}>
        <SectionTitle>💉 Context Poisoning Simulator</SectionTitle>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Inject adversarial documents to benchmark RAGShield's robustness. Tests how many poisoned chunks the shield blocks.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: '0.75rem', alignItems: 'end', marginBottom: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Test Query</label>
            <input className="input" value={poisonQuery} onChange={e => setPoisonQuery(e.target.value)} placeholder="Query to test..." />
          </div>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Poison Ratio</label>
            <select className="input" value={poisonRatio} onChange={e => setPoisonRatio(parseFloat(e.target.value))} style={{ width: 120 }}>
              <option value={0.1}>10%</option>
              <option value={0.2}>20%</option>
              <option value={0.3}>30%</option>
              <option value={0.5}>50%</option>
              <option value={0.7}>70%</option>
            </select>
          </div>
          <button className="btn btn-danger" onClick={runPoison} disabled={poisonLoading || !poisonQuery.trim()}>
            {poisonLoading ? <span className="spinner" /> : <><span>💉</span> Run Test</>}
          </button>
        </div>

        {poisonResult && !poisonResult.error && (
          <div className="scale-in" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', marginTop: '0.75rem' }}>
            {[
              { label: 'Injected Poison Chunks', value: poisonResult.benchmark?.total_poisoned_injected, color: 'var(--danger)' },
              { label: 'Baseline Exposed', value: poisonResult.benchmark?.baseline_poisoned_reach_llm, color: 'var(--warning)' },
              { label: 'Shield Blocked', value: poisonResult.benchmark?.shield_poisoned_blocked, color: 'var(--success)' },
              { label: 'Detection Rate', value: `${poisonResult.benchmark?.detection_rate_percent}%`, color: 'var(--brand-primary)' },
            ].map((item, i) => (
              <div key={i} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: '0.85rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.6rem', fontWeight: 900, color: item.color }}>{item.value ?? '—'}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>{item.label}</div>
              </div>
            ))}
            <div style={{ gridColumn: '1 / -1', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.85rem', color: 'var(--success)', fontWeight: 600 }}>
              ✅ {poisonResult.message}
            </div>
          </div>
        )}

        {poisonResult?.error && (
          <div style={{ color: 'var(--danger)', fontSize: '0.85rem', padding: '0.75rem', background: 'rgba(239,68,68,0.08)', borderRadius: 8 }}>
            ❌ {poisonResult.error}
          </div>
        )}
      </div>
    </div>
  )
}
