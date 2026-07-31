import React from 'react';
import { BookOpen, ShieldCheck, Cpu, Layers, FileText } from 'lucide-react';

const Research = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Banner */}
      <div style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(0,240,255,0.12), rgba(112,0,255,0.12))', borderRadius: '16px', border: '1px solid var(--border-color)', backdropFilter: 'blur(16px)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <BookOpen size={28} color="var(--primary)" />
          <h2 style={{ margin: 0, fontSize: '1.6rem' }}>RAGGuard-TR Research & Methodological Specification</h2>
        </div>
        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: 1.5 }}>
          Scientific specification of Retrieval Reliability Feature Extraction (RRFE) and Temporal Reliability & Risk Index (TRRI) calibration.
        </p>
      </div>

      {/* Grid of Research Sections */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        
        {/* Problem Statement */}
        <div style={{ padding: '24px', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--primary)' }}>1. Problem Statement</h3>
          <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            Standard RAG systems suffer from hallucination and temporal decay, returning outdated or contradictory information without reliability guarantees. Traditional confidence metrics fail to quantify temporal freshness or evidence consistency across retrieved document chunks.
          </p>
        </div>

        {/* RRFE Formulation */}
        <div style={{ padding: '24px', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--secondary)' }}>2. RRFE 5-Feature Vector</h3>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.86rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            <li style={{ marginBottom: '6px' }}><strong>Temporal Freshness (TFF):</strong> Exponential half-life decay (λ = ln(2) / 180 days).</li>
            <li style={{ marginBottom: '6px' }}><strong>Temporal Availability (TAF):</strong> Binary indicator of parseable publication date.</li>
            <li style={{ marginBottom: '6px' }}><strong>Source Credibility (SCF):</strong> Publication domain & publisher reputation score.</li>
            <li style={{ marginBottom: '6px' }}><strong>Evidence Consistency (ECF):</strong> Pairwise cosine similarity matrix among chunks.</li>
            <li><strong>Evidence Sufficiency (ESF):</strong> Normalized embedding coverage relative to query vector.</li>
          </ul>
        </div>

        {/* TRRI Definition */}
        <div style={{ padding: '24px', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--accent-green)' }}>3. TRRI & Decision Gate</h3>
          <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            TRRI is a continuous regression score in [0.0, 1.0] predicted by a trained XGBoost model. If any feature is missing (e.g. no publication date), the system strictly triggers <code>PredictionUnavailable</code> to maintain scientific integrity rather than outputting arbitrary constant defaults (0.5).
          </p>
        </div>

        {/* Technology Stack */}
        <div style={{ padding: '24px', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: 'var(--accent-yellow)' }}>4. System Architecture Stack</h3>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.86rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            <li style={{ marginBottom: '4px' }}><strong>Backend:</strong> FastAPI + Python 3.10 (Uvicorn async)</li>
            <li style={{ marginBottom: '4px' }}><strong>Vector DB:</strong> ChromaDB PersistentClient</li>
            <li style={{ marginBottom: '4px' }}><strong>Embeddings:</strong> nomic-embed-text</li>
            <li style={{ marginBottom: '4px' }}><strong>LLM Generator:</strong> Ollama (Qwen2.5:latest)</li>
            <li style={{ marginBottom: '4px' }}><strong>ML Regressor:</strong> XGBoost Regressor</li>
            <li><strong>Frontend:</strong> React + TypeScript + Vite</li>
          </ul>
        </div>

      </div>

    </div>
  );
};

export default Research;
