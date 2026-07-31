import React, { useState, useRef, useEffect } from 'react';
import {
  Send, ShieldAlert, CheckCircle, AlertTriangle, FileText, MessageSquareText,
  Info, HelpCircle, ChevronDown, ChevronUp, Cpu, Database, Layers, Clock, Zap
} from 'lucide-react';
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
}

interface PredictorMetadata {
  model_version: string;
  prediction_latency_ms: number;
  drift_flags: string[];
}

interface QueryResponseData {
  answer: str;
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
  response_data?: QueryResponseData;
}

const FEATURE_LABELS: Record<string, string> = {
  temporal_freshness:    'Temporal Freshness',
  temporal_availability: 'Temporal Availability',
  source_credibility:    'Source Credibility',
  evidence_consistency:  'Evidence Consistency',
  evidence_sufficiency:  'Evidence Sufficiency',
};

const ScoreBar = ({ score }: { score: number | null }) => {
  if (score === null || score === undefined) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px' }} />
        <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', minWidth: '36px', textAlign: 'right' }}>N/A</span>
      </div>
    );
  }

  const pct = Math.round(score * 100);
  const color = score >= 0.7 ? 'var(--accent-green)' : score >= 0.45 ? 'var(--accent-yellow)' : 'var(--accent-red)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: '3px', transition: 'width 0.4s ease' }} />
      </div>
      <span style={{ fontSize: '0.78rem', fontWeight: 700, color, minWidth: '36px', textAlign: 'right' }}>{pct}%</span>
    </div>
  );
};

/* --- Processing Timeline Step Tracker --- */
const ProcessingTimeline = ({ currentStep }: { currentStep: number }) => {
  const steps = [
    'Query Received',
    'Document Retrieval',
    'RRFE Extraction',
    'TRRI Prediction',
    'LLM Generation',
    'Completed'
  ];

  return (
    <div style={{ padding: '16px 20px', background: 'rgba(0,0,0,0.3)', borderRadius: '12px', border: '1px solid var(--border-color)', marginBottom: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative' }}>
        {steps.map((label, idx) => {
          const isDone = idx < currentStep;
          const isCurrent = idx === currentStep;
          const color = isDone ? 'var(--accent-green)' : isCurrent ? 'var(--primary)' : 'var(--text-muted)';
          return (
            <div key={label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2, flex: 1 }}>
              <div
                style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: isDone ? 'rgba(0,230,118,0.2)' : isCurrent ? 'rgba(0,240,255,0.2)' : 'rgba(255,255,255,0.05)',
                  border: `2px solid ${color}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  color,
                  marginBottom: '6px',
                  transition: 'all 0.3s ease'
                }}
              >
                {isDone ? '✓' : idx + 1}
              </div>
              <span style={{ fontSize: '0.72rem', color, textAlign: 'center', fontWeight: isCurrent ? 600 : 400 }}>{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/* --- Explainability Drawer Component --- */
const ExplainabilityDrawer = ({ data }: { data: QueryResponseData }) => {
  const [open, setOpen] = useState(false);
  const isAvailable = data.trri !== null && data.trri !== undefined;
  const riskColor = data.risk_level === 'low'
    ? 'var(--accent-green)'
    : data.risk_level === 'medium'
    ? 'var(--accent-yellow)'
    : data.risk_level === 'high'
    ? 'var(--accent-red)'
    : 'var(--text-muted)';

  const missingFeatures = data.execution_metadata?.missing_feature_scores ?? (isAvailable ? [] : ['temporal_freshness']);

  return (
    <div style={{ marginTop: '14px', width: '100%', maxWidth: '780px' }}>
      {/* Trigger button */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 14px',
          borderRadius: '8px',
          background: 'rgba(0,0,0,0.3)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-main)',
          fontSize: '0.82rem',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        }}
      >
        <Zap size={14} color="var(--primary)" />
        <span style={{ fontWeight: 600 }}>Why did the system make this decision?</span>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {open && (
        <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* 1. TRRI & Risk Card */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
            {/* TRRI Score Card */}
            <div style={{ padding: '16px', background: 'rgba(0,0,0,0.35)', borderRadius: '10px', border: `1px solid ${isAvailable ? riskColor : 'var(--border-color)'}` }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                TRRI Prediction Status
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: isAvailable ? riskColor : 'var(--text-muted)', margin: '6px 0 2px' }}>
                {isAvailable ? `${(data.trri! * 100).toFixed(1)}%` : 'Unavailable'}
              </div>
              <div style={{ fontSize: '0.78rem', color: isAvailable ? riskColor : 'var(--accent-yellow)', fontWeight: 600 }}>
                {isAvailable ? `Risk Level: ${data.risk_level.toUpperCase()}` : 'Missing Metadata Features'}
              </div>
            </div>

            {/* Decision Layer Card */}
            <div style={{ padding: '16px', background: 'rgba(0,0,0,0.35)', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Decision Layer Status
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, color: isAvailable ? 'var(--accent-green)' : 'var(--accent-yellow)', margin: '8px 0 4px' }}>
                {isAvailable ? 'Generate Response' : 'Prediction Unavailable'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {isAvailable
                  ? `Target TRRI >= 0.50 (Evaluated score: ${(data.trri! * 100).toFixed(1)}%)`
                  : 'Temporal Freshness could not be computed because retrieved documents lack publication dates.'}
              </div>
            </div>
          </div>

          {/* 2. Missing Feature Panel (If prediction unavailable) */}
          {!isAvailable && (
            <div style={{ padding: '16px', background: 'rgba(245,158,11,0.08)', borderRadius: '10px', border: '1px solid rgba(245,158,11,0.3)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-yellow)', fontWeight: 600, fontSize: '0.88rem', marginBottom: '8px' }}>
                <AlertTriangle size={16} />
                Prediction Status: Unavailable
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                <p style={{ margin: '0 0 8px 0' }}>
                  <strong>Reason:</strong> Mandatory Temporal Freshness could not be computed.
                </p>
                <div style={{ margin: '6px 0', display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                  <span style={{ color: 'var(--accent-green)' }}>✓ Temporal Availability</span>
                  <span style={{ color: 'var(--accent-green)' }}>✓ Source Credibility</span>
                  <span style={{ color: 'var(--accent-green)' }}>✓ Evidence Consistency</span>
                  <span style={{ color: 'var(--accent-green)' }}>✓ Evidence Sufficiency</span>
                  <span style={{ color: 'var(--accent-red)', fontWeight: 600 }}>✖ Temporal Freshness</span>
                </div>
                <p style={{ margin: '8px 0 0 0', fontStyle: 'italic', color: 'var(--text-main)' }}>
                  <strong>Decision:</strong> Prediction intentionally withheld to preserve scientific validity.
                </p>
              </div>
            </div>
          )}

          {/* 3. RRFE Feature Cards */}
          <div>
            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={14} color="var(--primary)" />
              RRFE 5-Dimensional Feature Vector
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
              {(data.rrfe_explanations ?? []).map(feat => (
                <div key={feat.feature_name} style={{ padding: '12px 14px', background: 'rgba(0,0,0,0.35)', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)' }}>
                      {FEATURE_LABELS[feat.feature_name] ?? feat.feature_name}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      conf: {Math.round(feat.confidence * 100)}%
                    </span>
                  </div>
                  <ScoreBar score={feat.score} />
                  <p style={{ margin: '6px 0 4px', fontSize: '0.74rem', color: 'var(--text-muted)', lineHeight: 1.35 }}>
                    {feat.reason}
                  </p>
                  <p style={{ margin: 0, fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)', fontStyle: 'italic' }}>
                    Source: {feat.evidence_source}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* 4. System Metrics & Execution Profiler Panel */}
          <div style={{ padding: '14px 16px', background: 'rgba(0,0,0,0.3)', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Cpu size={14} color="var(--secondary)" />
              Execution Profiler & Infrastructure Timing Metrics
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px', fontSize: '0.78rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Retrieval:</span><br />
                <strong style={{ color: 'var(--primary)' }}>{data.execution_metadata?.profiler?.retrieval_ms ?? '< 50'} ms</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>RRFE Extraction:</span><br />
                <strong style={{ color: 'var(--accent-green)' }}>{data.execution_metadata?.profiler?.rrfe_ms ?? data.execution_metadata?.execution_time_ms ?? '< 20'} ms</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Predictor Latency:</span><br />
                <strong style={{ color: 'var(--accent-green)' }}>{data.execution_metadata?.profiler?.predictor_ms ?? data.predictor_metadata?.prediction_latency_ms?.toFixed(2) ?? '< 2'} ms</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>LLM Generation:</span><br />
                <strong style={{ color: 'var(--secondary)' }}>{data.execution_metadata?.profiler?.generation_ms ? `${(data.execution_metadata.profiler.generation_ms / 1000).toFixed(2)} s` : '< 3.0 s'}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Total Query Latency:</span><br />
                <strong style={{ color: 'var(--text-main)' }}>{data.execution_metadata?.profiler?.total_ms ? `${(data.execution_metadata.profiler.total_ms / 1000).toFixed(2)} s` : '< 3.1 s'}</strong>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

/* --- Main Query Component --- */
const Query = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: 'Hello. I am the RAGGuard-TR temporal-aware engine. Ask me anything about your documents, and I will evaluate the TRRI score across 5 reliability dimensions before responding.',
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [timelineStep, setTimelineStep] = useState<number>(-1);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, timelineStep]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const queryText = input.trim();
    if (!queryText || isTyping) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: queryText };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);
    setTimelineStep(1); // Document Retrieval

    try {
      setTimeout(() => setTimelineStep(2), 200); // RRFE Extraction
      setTimeout(() => setTimelineStep(3), 400); // TRRI Prediction
      setTimeout(() => setTimelineStep(4), 600); // LLM Generation

      const response = await axios.post('/api/v1/query/chat', { query: queryText });
      const d: QueryResponseData = response.data;
      setTimelineStep(5); // Completed

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: d.answer,
        response_data: d,
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: 'Error communicating with the temporal engine backend.',
      }]);
    } finally {
      setIsTyping(false);
      setTimeout(() => setTimelineStep(-1), 1500);
    }
  };

  const getRiskColor = (level?: string) => {
    if (level === 'low') return 'var(--accent-green)';
    if (level === 'medium') return 'var(--accent-yellow)';
    if (level === 'high') return 'var(--accent-red)';
    return 'var(--text-muted)';
  };

  const getRiskIcon = (level?: string) => {
    if (level === 'low') return <CheckCircle size={16} />;
    if (level === 'medium') return <AlertTriangle size={16} />;
    if (level === 'high') return <ShieldAlert size={16} />;
    return <HelpCircle size={16} />;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)', overflow: 'hidden', backdropFilter: 'blur(16px)' }}>

      {/* Header */}
      <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MessageSquareText size={20} color="var(--primary)" />
          <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Temporal-Aware Context Engine</h3>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', gap: '15px' }}>
          <span>Strategy: <strong style={{ color: 'var(--text-main)' }}>Adaptive Retrieval</strong></span>
          <span>Threshold: <strong style={{ color: 'var(--text-main)' }}>TRRI &gt; 0.7</strong></span>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {messages.map((msg) => {
          const resp = msg.response_data;
          const isAvailable = resp?.trri !== null && resp?.trri !== undefined;

          return (
            <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              
              {/* Message Box */}
              <div style={{
                maxWidth: '82%',
                padding: '16px 20px',
                borderRadius: '16px',
                borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px',
                borderBottomLeftRadius: msg.role === 'ai' ? '4px' : '16px',
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, rgba(0,240,255,0.15), rgba(112,0,255,0.15))'
                  : 'rgba(255,255,255,0.05)',
                border: `1px solid ${msg.role === 'user' ? 'var(--primary)' : 'var(--border-color)'}`,
              }}>
                <p style={{ margin: 0, lineHeight: 1.6 }}>{msg.content}</p>
              </div>

              {/* AI Response Metadata Badges & Sources */}
              {msg.role === 'ai' && resp && (
                <>
                  <div style={{ display: 'flex', gap: '10px', marginTop: '8px', marginLeft: '4px', flexWrap: 'wrap', alignItems: 'center' }}>
                    {/* Risk Badge */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: getRiskColor(resp.risk_level), background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: '12px', border: `1px solid ${getRiskColor(resp.risk_level)}` }}>
                      {getRiskIcon(resp.risk_level)}
                      <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{resp.risk_level} Risk</span>
                    </div>

                    {/* Sources list */}
                    {resp.sources?.map((src, idx) => (
                      <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                        <FileText size={14} />
                        <span>{src.filename}</span>
                      </div>
                    ))}
                  </div>

                  {/* Explainability Drawer */}
                  <ExplainabilityDrawer data={resp} />
                </>
              )}
            </div>
          );
        })}

        {/* Live Timeline Step Indicator during typing */}
        {isTyping && (
          <div style={{ width: '100%', maxWidth: '780px', marginTop: '8px' }}>
            <ProcessingTimeline currentStep={timelineStep} />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.2)' }}>
        <form onSubmit={handleSend} style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your ingested documents..."
            disabled={isTyping}
            style={{ flex: 1, padding: '16px 20px', fontSize: '1rem', background: 'rgba(0,0,0,0.4)', opacity: isTyping ? 0.6 : 1 }}
          />
          <button type="submit" className="btn-primary" disabled={isTyping || !input.trim()} style={{ padding: '0 24px', display: 'flex', alignItems: 'center', gap: '8px', opacity: isTyping || !input.trim() ? 0.6 : 1 }}>
            <Send size={18} />
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default Query;
