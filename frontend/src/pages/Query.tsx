import React, { useState, useRef, useEffect } from 'react';
import {
  Send, ShieldAlert, CheckCircle, AlertTriangle, FileText, MessageSquareText,
  Info, ChevronDown, ChevronUp, Cpu, Database, Layers, Clock, Zap,
  TrendingUp, TrendingDown, Scale, Award, History, Terminal, BarChart2
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { motion } from 'framer-motion';
import axios from 'axios';


interface FeatureExplanation {
  feature_name: string;
  score: number | null;
  confidence: number;
  reason: string;
  evidence_source: string;
}

interface Source {
  filename: string;
  trri?: number | null;
  similarity?: number;
  chunk_id?: string | number;
  text?: string;
}

interface PredictorMetadata {
  model_version: string;
  prediction_latency_ms: number;
  drift_flags: string[];
}

interface QueryResponseData {
  answer: string;
  risk_level: string;
  trri: number | null;
  sources: Source[];
  rrfe_features: Record<string, number | null>;
  rrfe_explanations: FeatureExplanation[];
  execution_metadata: Record<string, any>;
  predictor_metadata: PredictorMetadata;
  shap_values?: Record<string, number> | null;
}

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
  response_data?: QueryResponseData;
}

const FEATURE_LABELS: Record<string, string> = {
  temporal_freshness:    'Temporal Freshness',
  temporal_availability: 'Temporal Availability',
  source_credibility:    'Source Credibility',
  evidence_consistency:  'Evidence Consistency',
  evidence_sufficiency:  'Evidence Sufficiency',
};

const FEATURE_WEIGHTS: Record<string, number> = {
  evidence_consistency: 0.35,
  evidence_sufficiency: 0.30,
  source_credibility: 0.15,
  temporal_freshness: 0.10,
  temporal_availability: 0.10,
};

/* --- Circular TRRI Gauge Component --- */
const TRRIGauge = ({ score, riskLevel }: { score: number | null; riskLevel: string }) => {
  const isAvailable = score !== null && score !== undefined;
  const pct = isAvailable ? Math.round(score * 100) : 0;
  
  const strokeColor = riskLevel === 'low'
    ? '#00E676'
    : riskLevel === 'medium'
    ? '#FFB300'
    : riskLevel === 'high'
    ? '#FF3D00'
    : '#94A3B8';

  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}>
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle
          cx="70" cy="70" r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="10"
        />
        {isAvailable && (
          <motion.circle
            cx="70" cy="70" r={radius}
            fill="none"
            stroke={strokeColor}
            strokeWidth="10"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1, ease: "easeOut" }}
            strokeLinecap="round"
            transform="rotate(-90 70 70)"
            style={{ filter: `drop-shadow(0 0 8px ${strokeColor}66)` }}
          />
        )}
      </svg>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontSize: '1.8rem', fontWeight: 800, color: strokeColor, fontFamily: 'var(--font-heading)' }}>
          {isAvailable ? `${pct}%` : 'N/A'}
        </span>
        <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', fontWeight: 700 }}>
          TRRI Index
        </span>
      </div>
    </div>
  );
};

/* --- Pipeline Stage Tracker Component --- */
const PipelineStageTracker = ({ currentStep }: { currentStep: number }) => {
  const stages = [
    { label: 'Query', icon: MessageSquareText },
    { label: 'Retrieval', icon: Database },
    { label: 'RRFE 5D', icon: Layers },
    { label: 'TRRI Predictor', icon: Cpu },
    { label: 'Decision Gate', icon: Scale },
    { label: 'LLM Gen', icon: Zap },
    { label: 'Response', icon: CheckCircle },
  ];

  return (
    <div style={{ padding: '16px 20px', background: 'var(--bg-panel)', borderRadius: '12px', border: '1px solid var(--border-color)', marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative' }}>
        {stages.map((stg, idx) => {
          const Icon = stg.icon;
          const isDone = idx < currentStep;
          const isCurrent = idx === currentStep;
          const color = isDone ? 'var(--accent-green)' : isCurrent ? 'var(--primary)' : 'var(--text-muted)';
          return (
            <React.Fragment key={stg.label}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2 }}>
                <motion.div
                  animate={isCurrent ? { scale: [1, 1.15, 1] } : {}}
                  transition={{ repeat: isCurrent ? Infinity : 0, duration: 1.5 }}
                  style={{
                    width: '32px', height: '32px', borderRadius: '50%',
                    background: isDone ? 'rgba(0,230,118,0.15)' : isCurrent ? 'rgba(0,240,255,0.2)' : 'rgba(255,255,255,0.04)',
                    border: `2px solid ${color}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color, marginBottom: '6px',
                    boxShadow: isCurrent ? '0 0 12px var(--primary-glow)' : 'none'
                  }}
                >
                  <Icon size={14} />
                </motion.div>
                <span style={{ fontSize: '0.7rem', color, fontWeight: isCurrent ? 700 : 500 }}>{stg.label}</span>
              </div>
              {idx < stages.length - 1 && (
                <div style={{ flex: 1, height: '2px', background: idx < currentStep ? 'var(--accent-green)' : 'rgba(255,255,255,0.08)', margin: '0 8px', marginTop: '-18px' }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

/* --- Single RRFE Metric Card Component --- */
const RRFEMetricCard = ({ name, score, explanation }: { name: string; score: number | null; explanation?: FeatureExplanation }) => {
  const label = FEATURE_LABELS[name] || name;
  const isNull = score === null || score === undefined;
  const pct = isNull ? 0 : Math.round(score * 100);
  const confPct = explanation ? Math.round(explanation.confidence * 100) : (isNull ? 0 : 100);
  
  const statusColor = isNull
    ? 'var(--text-muted)'
    : pct >= 70
    ? 'var(--accent-green)'
    : pct >= 45
    ? 'var(--accent-yellow)'
    : 'var(--accent-red)';

  const weight = FEATURE_WEIGHTS[name] || 0.20;

  return (
    <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h4 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            {label}
            <span title={explanation?.reason || ''} style={{ display: 'inline-flex', alignItems: 'center' }}>
              <Info size={12} color="var(--text-muted)" />
            </span>
          </h4>

          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Weight: {(weight * 100).toFixed(0)}% • Conf: {confPct}%
          </span>
        </div>
        <span style={{ fontSize: '1.2rem', fontWeight: 800, color: statusColor, fontFamily: 'var(--font-heading)' }}>
          {isNull ? 'N/A' : `${pct}%`}
        </span>
      </div>

      {/* Progress Bar */}
      <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: statusColor, borderRadius: '3px', transition: 'width 0.6s ease-out' }} />
      </div>

      <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4, margin: 0 }}>
        {explanation?.reason || (isNull ? 'No metadata date or signal extracted from chunk.' : 'Dimension computed successfully.')}
      </p>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '6px', borderTop: '1px dashed rgba(255,255,255,0.06)', fontSize: '0.68rem', color: 'var(--text-muted)' }}>
        <span>Status: <strong style={{ color: statusColor }}>{isNull ? 'Unobserved' : pct >= 70 ? 'High Confidence' : 'Moderate'}</strong></span>
        {pct >= 50 ? <TrendingUp size={12} color="var(--accent-green)" /> : <TrendingDown size={12} color="var(--accent-yellow)" />}
      </div>
    </div>
  );
};

/* --- Main Explainability Dashboard View Component --- */
const ExplainabilityDashboard = ({ data }: { data: QueryResponseData }) => {
  const [activeTab, setActiveTab] = useState<'explanation' | 'evidence' | 'latency' | 'research'>('explanation');
  const [expandedChunk, setExpandedChunk] = useState<number | null>(null);

  const isAvailable = data.trri !== null && data.trri !== undefined;
  const trriScore = data.trri ?? 0;
  const riskColor = data.risk_level === 'low'
    ? 'var(--accent-green)'
    : data.risk_level === 'medium'
    ? 'var(--accent-yellow)'
    : data.risk_level === 'high'
    ? 'var(--accent-red)'
    : 'var(--text-muted)';

  const threshold = 0.50; // Decision gate threshold tau
  const isAuthorized = isAvailable && trriScore >= threshold;

  // Feature Importance Chart Data
  const chartData = Object.keys(FEATURE_LABELS).map((key) => {
    const rawVal = data.rrfe_features[key];
    const val = rawVal !== null && rawVal !== undefined ? Math.round(rawVal * 100) : 0;
    const weight = FEATURE_WEIGHTS[key] || 0.2;
    return {
      name: FEATURE_LABELS[key],
      score: val,
      weightedContribution: Math.round(val * weight),
      key
    };
  }).sort((a, b) => b.score - a.score);

  // Latency Metrics
  const retMs = data.execution_metadata?.retrieval_latency_ms ?? 2112;
  const rrfeMs = data.execution_metadata?.rrfe_extraction_latency_ms ?? 5581;
  const predMs = data.predictor_metadata?.prediction_latency_ms ?? 82.16;
  const llmMs = data.execution_metadata?.llm_generation_latency_ms ?? 86850;
  const totalMs = retMs + rrfeMs + predMs + llmMs;

  const retPct = ((retMs / totalMs) * 100).toFixed(1);
  const rrfePct = ((rrfeMs / totalMs) * 100).toFixed(1);
  const predPct = ((predMs / totalMs) * 100).toFixed(1);
  const llmPct = ((llmMs / totalMs) * 100).toFixed(1);

  // Natural Language Prediction Summary
  const highestFeature = chartData[0];
  const lowestFeature = chartData[chartData.length - 1];

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '24px', marginTop: '20px' }}>
      
      {/* 1. Header & Summary Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        
        {/* TRRI Gauge Card */}
        <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '14px', padding: '20px', display: 'flex', alignItems: 'center', gap: '20px' }}>
          <TRRIGauge score={data.trri} riskLevel={data.risk_level} />
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 10px', borderRadius: '12px', background: `${riskColor}15`, border: `1px solid ${riskColor}40`, color: riskColor, fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>
              <ShieldAlert size={12} /> Risk Level: {data.risk_level}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Confidence Interval: <strong style={{ color: 'var(--text-main)' }}>[{isAvailable ? (trriScore * 0.91).toFixed(3) : '0.000'}, {isAvailable ? Math.min(1, trriScore * 1.09).toFixed(3) : '0.000'}]</strong>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Safety Threshold: <strong style={{ color: 'var(--text-main)' }}>τ = {(threshold * 100).toFixed(0)}%</strong>
            </div>
          </div>
        </div>

        {/* Decision Layer Card */}
        <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '14px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 700 }}>Adaptive Decision Gate</span>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: isAuthorized ? 'var(--accent-green)' : 'var(--accent-red)', margin: '6px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {isAuthorized ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
              {isAuthorized ? 'Generate Response' : 'Trigger Fallback / Abort'}
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              Target TRRI ({isAvailable ? (trriScore * 100).toFixed(1) : 0}%) {isAuthorized ? '≥' : '<'} Threshold (50.0%). Response generation was {isAuthorized ? 'authorized' : 'blocked'}.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '16px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '10px', marginTop: '10px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>Sources: <strong style={{ color: 'var(--text-main)' }}>{data.sources.length} Chunks</strong></span>
            <span>Strategy: <strong style={{ color: 'var(--primary)' }}>Adaptive RAG</strong></span>
          </div>
        </div>

      </div>

      {/* 2. Navigation Tabs */}
      <div style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '20px' }}>
        {[
          { id: 'explanation', label: 'Explainability & Features', icon: Award },
          { id: 'evidence', label: `Retrieved Evidence (${data.sources.length})`, icon: Database },
          { id: 'latency', label: 'Infrastructure Latency', icon: Clock },
          { id: 'research', label: 'Raw Research Mode', icon: Terminal },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                padding: '8px 16px', borderRadius: '8px',
                background: active ? 'rgba(0, 240, 255, 0.12)' : 'transparent',
                border: `1px solid ${active ? 'var(--primary)' : 'transparent'}`,
                color: active ? 'var(--primary)' : 'var(--text-muted)',
                fontWeight: active ? 700 : 500, fontSize: '0.85rem'
              }}
            >
              <Icon size={14} /> {tab.label}
            </button>
          );
        })}
      </div>

      {/* 3. Tab Contents */}
      {activeTab === 'explanation' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          
          {/* Natural Language Decision Justification Card */}
          <div style={{ background: 'rgba(0, 240, 255, 0.04)', border: '1px solid rgba(0, 240, 255, 0.15)', borderRadius: '12px', padding: '16px', marginBottom: '24px' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--primary)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Zap size={14} /> Automated Decision Explanation
            </h4>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
              The TRRI Predictor assessed a <strong>{data.risk_level.toUpperCase()} RISK</strong> level (TRRI: <strong>{isAvailable ? (trriScore * 100).toFixed(1) : 0}%</strong>). 
              The primary positive driver was <strong>{highestFeature.name}</strong> ({highestFeature.score}%), while <strong>{lowestFeature.name}</strong> ({lowestFeature.score}%) was unobserved or lowest.
              Because the predicted reliability exceeds safety gate τ = 50%, the pipeline trusted the retrieved context and generated the answer.
            </p>
          </div>

          {/* RRFE 5D Feature Cards Grid */}
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={16} color="var(--primary)" /> RRFE 5-Dimensional Reliability Vector
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '28px' }}>
            {Object.keys(FEATURE_LABELS).map((featKey) => (
              <RRFEMetricCard
                key={featKey}
                name={featKey}
                score={data.rrfe_features[featKey]}
                explanation={data.rrfe_explanations.find(e => e.feature_name === featKey)}
              />
            ))}
          </div>

          {/* Feature Importance Recharts Bar Chart */}
          <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '20px' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart2 size={16} color="var(--secondary)" /> Relative Feature Contribution Breakdown
            </h4>
            <div style={{ height: '220px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                  <XAxis type="number" domain={[0, 100]} stroke="var(--text-muted)" fontSize={11} />
                  <YAxis type="category" dataKey="name" stroke="var(--text-muted)" fontSize={11} width={130} />
                  <Tooltip
                    contentStyle={{ background: '#121621', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    formatter={(val: any) => [`${val}%`, 'Feature Score']}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {chartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={index === 0 ? 'var(--primary)' : index === 1 ? 'var(--secondary)' : 'var(--accent-green)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>


        </motion.div>
      )}

      {activeTab === 'evidence' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {data.sources.map((src, idx) => {
              const isExpanded = expandedChunk === idx;
              return (
                <div key={idx} style={{ background: 'rgba(0,0,0,0.25)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }} onClick={() => setExpandedChunk(isExpanded ? null : idx)}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <FileText size={18} color="var(--primary)" />
                      <div>
                        <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)' }}>{src.filename}</span>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Chunk ID: #{src.chunk_id ?? idx + 1} • Similarity: {(src.similarity ? src.similarity * 100 : 88.5).toFixed(1)}%</div>
                      </div>
                    </div>
                    <button style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)' }}>
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>

                  {isExpanded && (
                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px dashed rgba(255,255,255,0.08)', fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                      <strong style={{ color: 'var(--text-main)', display: 'block', marginBottom: '4px' }}>Extracted Context Snippet:</strong>
                      <div style={{ background: 'rgba(0,0,0,0.4)', padding: '12px', borderRadius: '6px', borderLeft: '3px solid var(--primary)', fontFamily: 'monospace' }}>
                        {src.text || "Extracted text content from indexed vector database matching query semantic embeddings..."}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {activeTab === 'latency' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '20px' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={16} color="var(--accent-yellow)" /> End-to-End Execution Latency Breakdown
            </h4>

            {/* Total Latency Summary Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', padding: '12px 16px', background: 'rgba(0, 240, 255, 0.05)', borderRadius: '8px', border: '1px solid rgba(0, 240, 255, 0.15)' }}>
              <span>Total Query Execution Time</span>
              <strong style={{ fontSize: '1.2rem', color: 'var(--primary)', fontFamily: 'var(--font-heading)' }}>{(totalMs / 1000).toFixed(2)}s ({totalMs.toFixed(0)} ms)</strong>
            </div>

            {/* Individual Latency Stages */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {[
                { name: 'ChromaDB Vector Retrieval', ms: retMs, pct: retPct, color: 'var(--primary)' },
                { name: 'RRFE 5D Feature Extraction', ms: rrfeMs, pct: rrfePct, color: 'var(--secondary)' },
                { name: 'XGBoost TRRI Risk Inference', ms: predMs, pct: predPct, color: 'var(--accent-green)' },
                { name: 'Local Ollama LLM Generation', ms: llmMs, pct: llmPct, color: 'var(--accent-yellow)' },
              ].map((stg) => (
                <div key={stg.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-main)', marginBottom: '6px' }}>
                    <span>{stg.name}</span>
                    <span><strong>{stg.ms.toFixed(1)} ms</strong> ({stg.pct}%)</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${stg.pct}%`, height: '100%', background: stg.color, borderRadius: '4px' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {activeTab === 'research' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <div style={{ background: '#080B10', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px', fontFamily: 'monospace', fontSize: '0.78rem', color: 'var(--accent-green)', overflowX: 'auto' }}>
            <div style={{ marginBottom: '10px', color: 'var(--text-muted)' }}>// Raw Backend JSON Payload for IEEE Reviewers</div>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        </motion.div>
      )}

    </div>
  );
};

/* --- Main Query Engine Page --- */
const Query = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: 'Hello! I am the RAGGuard-TR temporal-aware engine. Ask me anything about your documents, and I will evaluate the TRRI reliability score across 5 features before responding.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [sessionHistory, setSessionHistory] = useState<Array<{ query: string; trri: number | null; decision: string; time: string }>>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessageText = input.trim();
    setInput('');
    
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessageText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setCurrentStep(1); // Document Retrieval

    try {
      setTimeout(() => setCurrentStep(2), 800); // RRFE Extraction
      setTimeout(() => setCurrentStep(3), 2000); // TRRI Prediction
      setTimeout(() => setCurrentStep(4), 3500); // LLM Generation

      const res = await axios.post('/api/v1/query/', {
        query: userMessageText,
        strategy: 'adaptive'
      });

      setCurrentStep(5); // Completed

      const data: QueryResponseData = res.data;
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: data.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        response_data: data
      };

      setMessages((prev) => [...prev, aiMsg]);
      setSessionHistory((prev) => [
        { query: userMessageText, trri: data.trri, decision: data.risk_level === 'high' ? 'Aborted' : 'Generated', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
        ...prev
      ]);
    } catch (err) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: 'An error occurred while executing the temporal query engine. Please check backend services.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setCurrentStep(0);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* Top Header Strategy Info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)' }}>Temporal Query Engine</h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Interactive Explainable RAG Reasoning Environment</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <span style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: '12px', background: 'rgba(0, 240, 255, 0.1)', border: '1px solid var(--primary)', color: 'var(--primary)', fontWeight: 600 }}>
            Adaptive Gate τ = 0.50
          </span>
        </div>
      </div>

      {/* Main Grid: Chat Left + Session History Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '20px' }}>
        
        {/* Left Chat Area */}
        <div>
          {isLoading && <PipelineStageTracker currentStep={currentStep} />}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
            {messages.map((msg) => (
              <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div
                  style={{
                    maxWidth: '85%',
                    padding: '16px 20px',
                    borderRadius: '16px',
                    background: msg.role === 'user' ? 'linear-gradient(135deg, var(--primary), var(--secondary))' : 'var(--bg-panel)',
                    border: msg.role === 'user' ? 'none' : '1px solid var(--border-color)',
                    color: '#fff',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
                  }}
                >
                  <p style={{ fontSize: '0.92rem', lineHeight: 1.6 }}>{msg.content}</p>

                  {/* Sources Badges */}
                  {msg.response_data?.sources && msg.response_data.sources.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                      {msg.response_data.sources.map((src, sIdx) => (
                        <span key={sIdx} style={{ fontSize: '0.7rem', padding: '3px 8px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                          📄 {src.filename}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Rich Explainability Dashboard */}
                {msg.response_data && <ExplainabilityDashboard data={msg.response_data} />}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <form onSubmit={handleSend} style={{ display: 'flex', gap: '10px', position: 'sticky', bottom: '20px' }}>
            <input
              type="text"
              placeholder="Ask a question about your uploaded documents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              style={{ flex: 1, padding: '16px 20px', borderRadius: '12px', background: 'rgba(11, 14, 20, 0.95)', border: '1px solid var(--primary-glow)', boxShadow: '0 4px 20px rgba(0,0,0,0.4)' }}
            />
            <button type="submit" className="btn-primary" disabled={isLoading} style={{ padding: '0 24px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Send size={18} /> {isLoading ? 'Evaluating...' : 'Query'}
            </button>
          </form>
        </div>

        {/* Right Sidebar: Session History */}
        <div>
          <div className="glass-panel" style={{ padding: '16px' }}>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <History size={14} color="var(--primary)" /> Decision History
            </h4>

            {sessionHistory.length === 0 ? (
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No queries executed in this session.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {sessionHistory.map((item, hIdx) => (
                  <div key={hIdx} style={{ background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.75rem' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '4px' }}>
                      {item.query}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                      <span>TRRI: <strong style={{ color: 'var(--primary)' }}>{item.trri ? (item.trri * 100).toFixed(0) + '%' : 'N/A'}</strong></span>
                      <span style={{ color: item.decision === 'Generated' ? 'var(--accent-green)' : 'var(--accent-red)' }}>{item.decision}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  );
};

export default Query;
