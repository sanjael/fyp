import { BookOpen, BarChart2, Activity } from 'lucide-react';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';

const Research = () => {

  const featureImportanceData = [
    { feature: 'Evidence Consistency', importance: 0.35, color: 'var(--primary)' },
    { feature: 'Evidence Sufficiency', importance: 0.30, color: 'var(--secondary)' },
    { feature: 'Source Credibility', importance: 0.15, color: 'var(--accent-green)' },
    { feature: 'Temporal Freshness', importance: 0.10, color: 'var(--accent-yellow)' },
    { feature: 'Temporal Availability', importance: 0.10, color: 'var(--accent-red)' },
  ];

  const failureCategoriesData = [
    { name: 'Missing Publication Date', value: 45, color: '#FFB300' },
    { name: 'Low Semantic Sufficiency', value: 30, color: '#FF3D00' },
    { name: 'Cross-Chunk Contradiction', value: 15, color: '#7000FF' },
    { name: 'Unverified Domain Source', value: 10, color: '#00F0FF' },
  ];

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* Header Banner */}
      <div style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(0,240,255,0.12), rgba(112,0,255,0.12))', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <BookOpen size={28} color="var(--primary)" />
          <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 800 }}>RAGGuard-TR IEEE Research & Methodological Specification</h2>
        </div>
        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
          Scientific formulation of Retrieval Reliability Feature Extraction (RRFE) and Temporal Reliability & Risk Index (TRRI) calibration.
        </p>
      </div>

      {/* Visual Analytics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        {/* XGBoost Feature Importance Bar Chart */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart2 size={18} color="var(--primary)" /> XGBoost Feature Importance Weights (Gini Gain)
          </h3>
          <div style={{ height: '220px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={featureImportanceData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                <XAxis type="number" domain={[0, 0.4]} stroke="var(--text-muted)" fontSize={11} />
                <YAxis type="category" dataKey="feature" stroke="var(--text-muted)" fontSize={11} width={130} />
                <Tooltip contentStyle={{ background: '#121621', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                  {featureImportanceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Failure Categories Breakdown */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="var(--accent-red)" /> Risk Trigger & Failure Mode Distribution
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', height: '200px' }}>
            <div style={{ width: '50%', height: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={failureCategoriesData} cx="50%" cy="50%" innerRadius={40} outerRadius={65} dataKey="value">
                    {failureCategoriesData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#121621', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '50%', fontSize: '0.78rem' }}>
              {failureCategoriesData.map((item) => (
                <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: item.color }} />
                  <span style={{ color: 'var(--text-muted)' }}>{item.name}:</span>
                  <strong style={{ color: 'var(--text-main)' }}>{item.value}%</strong>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* Grid of Research Methodological Specifications */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        
        {/* Problem Statement */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--primary)' }}>1. Problem Statement</h3>
          <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            Standard RAG systems suffer from hallucination and temporal decay, returning outdated or contradictory information without reliability guarantees. Traditional confidence metrics fail to quantify temporal freshness or evidence consistency across retrieved document chunks.
          </p>
        </div>

        {/* RRFE Formulation */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--secondary)' }}>2. RRFE 5-Feature Vector</h3>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.86rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            <li style={{ marginBottom: '6px' }}><strong>Temporal Freshness (TFF):</strong> Exponential half-life decay ($\lambda = \ln(2) / 180$ days).</li>
            <li style={{ marginBottom: '6px' }}><strong>Temporal Availability (TAF):</strong> Binary indicator of parseable publication date.</li>
            <li style={{ marginBottom: '6px' }}><strong>Source Credibility (SCF):</strong> Publication domain & publisher reputation score.</li>
            <li style={{ marginBottom: '6px' }}><strong>Evidence Consistency (ECF):</strong> Pairwise cosine similarity matrix among chunks.</li>
            <li><strong>Evidence Sufficiency (ESF):</strong> Normalized embedding coverage relative to query vector.</li>
          </ul>
        </div>

        {/* TRRI Definition */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--accent-green)' }}>3. TRRI & Decision Gate</h3>
          <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            TRRI is a continuous regression score in $[0.0, 1.0]$ predicted by a trained XGBoost model. If any feature is missing (e.g. no publication date), XGBoost handles NaNs natively via <code>missing=np.nan</code> to maintain scientific integrity rather than outputting arbitrary constant defaults.
          </p>
        </div>

        {/* Technology Stack */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--accent-yellow)' }}>4. System Architecture Stack</h3>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.86rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            <li style={{ marginBottom: '4px' }}><strong>Backend:</strong> FastAPI + Python 3.10 (Uvicorn async)</li>
            <li style={{ marginBottom: '4px' }}><strong>Vector DB:</strong> ChromaDB PersistentClient</li>
            <li style={{ marginBottom: '4px' }}><strong>Embeddings:</strong> nomic-embed-text</li>
            <li style={{ marginBottom: '4px' }}><strong>LLM Generator:</strong> Ollama (Qwen2.5:latest)</li>
            <li style={{ marginBottom: '4px' }}><strong>ML Regressor:</strong> XGBoost Regressor</li>
            <li><strong>Frontend:</strong> React + TypeScript + Vite + Recharts</li>
          </ul>
        </div>

      </div>

    </div>
  );
};

export default Research;
