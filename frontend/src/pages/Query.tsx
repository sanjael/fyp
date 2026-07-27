import React, { useState, useRef, useEffect } from 'react';
import { Send, ShieldAlert, CheckCircle, AlertTriangle, FileText, MessageSquareText, Info } from 'lucide-react';
import axios from 'axios';

interface FeatureExplanation {
  feature_name: string;
  score: number;
  confidence: number;
  reason: string;
  evidence_source: string;
}

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  riskLevel?: 'low' | 'medium' | 'high';
  trri?: number;
  sources?: { filename: string; trri: number }[];
  rrfe_explanations?: FeatureExplanation[];
}

const FEATURE_LABELS: Record<string, string> = {
  temporal_freshness:    'Temporal Freshness',
  temporal_availability: 'Temporal Availability',
  source_credibility:    'Source Credibility',
  evidence_consistency:  'Evidence Consistency',
  evidence_sufficiency:  'Evidence Sufficiency',
};

const ScoreBar = ({ score }: { score: number }) => {
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

const ExplainabilityPanel = ({ explanations, trri, riskLevel }: {
  explanations: FeatureExplanation[];
  trri?: number;
  riskLevel?: string;
}) => {
  const [open, setOpen] = useState(false);
  if (!explanations || explanations.length === 0) return null;

  const riskColor = riskLevel === 'low' ? 'var(--accent-green)' : riskLevel === 'medium' ? 'var(--accent-yellow)' : 'var(--accent-red)';

  return (
    <div style={{ marginTop: '10px', width: '100%', maxWidth: '680px' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
      >
        <Info size={14} />
        {open ? 'Hide' : 'Show'} TRRI Explainability
        {trri !== undefined && (
          <span style={{ marginLeft: '8px', color: riskColor, fontWeight: 700 }}>TRRI: {(trri * 100).toFixed(1)}%</span>
        )}
      </button>

      {open && (
        <div style={{ marginTop: '10px', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
          {explanations.map(feat => (
            <div key={feat.feature_name} style={{ padding: '14px 16px', background: 'rgba(0,0,0,0.35)', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  {FEATURE_LABELS[feat.feature_name] ?? feat.feature_name}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  conf: {Math.round(feat.confidence * 100)}%
                </span>
              </div>
              <ScoreBar score={feat.score} />
              <p style={{ margin: '8px 0 4px', fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                {feat.reason}
              </p>
              <p style={{ margin: 0, fontSize: '0.72rem', color: 'rgba(255,255,255,0.3)', fontStyle: 'italic' }}>
                Source: {feat.evidence_source}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const Query = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: 'Hello. I am the RAGGuard-TR temporal-aware engine. Ask me anything about your documents, and I will evaluate the TRRI score across 5 reliability dimensions before responding.',
      riskLevel: 'low',
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await axios.post('/api/v1/query/chat', { query: input });
      const d = response.data;
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: d.answer,
        riskLevel: d.risk_level,
        trri: d.trri,
        sources: d.sources,
        rrfe_explanations: d.rrfe_explanations ?? [],
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: 'Error communicating with the temporal engine backend.',
        riskLevel: 'high',
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const getRiskColor = (level?: string) =>
    level === 'low' ? 'var(--accent-green)' : level === 'medium' ? 'var(--accent-yellow)' : 'var(--accent-red)';

  const getRiskIcon = (level?: string) => {
    if (level === 'low') return <CheckCircle size={16} />;
    if (level === 'medium') return <AlertTriangle size={16} />;
    return <ShieldAlert size={16} />;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)', overflow: 'hidden', backdropFilter: 'blur(16px)' }}>

      {/* Header */}
      <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MessageSquareText size={20} color="var(--primary)" />
          <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Query Engine</h3>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', gap: '15px' }}>
          <span>Strategy: <strong style={{ color: 'var(--text-main)' }}>Adaptive Retrieval</strong></span>
          <span>Threshold: <strong style={{ color: 'var(--text-main)' }}>TRRI &gt; 0.7</strong></span>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {messages.map((msg) => (
          <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '80%',
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

            {msg.role === 'ai' && (
              <>
                {/* Risk badge + sources */}
                <div style={{ display: 'flex', gap: '12px', marginTop: '8px', marginLeft: '8px', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: getRiskColor(msg.riskLevel), background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: '12px', border: `1px solid ${getRiskColor(msg.riskLevel)}` }}>
                    {getRiskIcon(msg.riskLevel)}
                    <span style={{ textTransform: 'capitalize' }}>{msg.riskLevel} Risk</span>
                  </div>
                  {msg.sources?.map((src, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                      <FileText size={14} />
                      <span>{src.filename}</span>
                    </div>
                  ))}
                </div>

                {/* Explainability panel */}
                <ExplainabilityPanel
                  explanations={msg.rrfe_explanations ?? []}
                  trri={msg.trri}
                  riskLevel={msg.riskLevel}
                />
              </>
            )}
          </div>
        ))}

        {isTyping && (
          <div style={{ alignSelf: 'flex-start', color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
            RAGGuard is evaluating TRRI across 5 dimensions...
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
            style={{ flex: 1, padding: '16px 20px', fontSize: '1rem', background: 'rgba(0,0,0,0.4)' }}
          />
          <button type="submit" className="btn-primary" style={{ padding: '0 24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Send size={18} />
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default Query;


interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  riskLevel?: 'low' | 'medium' | 'high';
  sources?: { filename: string; trri: number }[];
}

const Query = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: 'Hello. I am the RAGGuard-TR temporal-aware engine. Ask me anything about your documents, and I will evaluate the Context Quality Score (CQS) and TRRI before responding.',
      riskLevel: 'low'
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await axios.post('/api/v1/query/chat', { query: input });
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: response.data.answer,
        riskLevel: response.data.risk_level,
        sources: response.data.sources
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: 'Error communicating with the temporal engine backend.',
        riskLevel: 'high'
      }]);
    } finally {
      setIsTyping(false);
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
    return null;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)', overflow: 'hidden', backdropFilter: 'blur(16px)' }}>
      
      {/* Header */}
      <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MessageSquareText size={20} color="var(--primary)" />
          <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Query Engine</h3>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', gap: '15px' }}>
          <span>Strategy: <strong style={{ color: 'var(--text-main)' }}>Adaptive Retrieval</strong></span>
          <span>Threshold: <strong style={{ color: 'var(--text-main)' }}>TRRI &gt; 0.7</strong></span>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {messages.map((msg) => (
          <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            
            <div style={{ 
              maxWidth: '80%', 
              padding: '16px 20px', 
              borderRadius: '16px',
              borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px',
              borderBottomLeftRadius: msg.role === 'ai' ? '4px' : '16px',
              background: msg.role === 'user' ? 'linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(112, 0, 255, 0.15))' : 'rgba(255,255,255,0.05)',
              border: `1px solid ${msg.role === 'user' ? 'var(--primary)' : 'var(--border-color)'}`,
            }}>
              <p style={{ margin: 0, lineHeight: 1.6 }}>{msg.content}</p>
            </div>

            {msg.role === 'ai' && (
              <div style={{ display: 'flex', gap: '12px', marginTop: '8px', marginLeft: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: getRiskColor(msg.riskLevel), background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: '12px', border: `1px solid ${getRiskColor(msg.riskLevel)}` }}>
                  {getRiskIcon(msg.riskLevel)}
                  <span style={{ textTransform: 'capitalize' }}>{msg.riskLevel} Risk</span>
                </div>
                
                {msg.sources && msg.sources.map((src, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                    <FileText size={14} />
                    <span>{src.filename}</span>
                    <span style={{ color: 'var(--primary)', fontWeight: 600 }}>[TRRI: {src.trri}]</span>
                  </div>
                ))}
              </div>
            )}
            
          </div>
        ))}
        {isTyping && (
          <div style={{ alignSelf: 'flex-start', color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
            RAGGuard is evaluating TRRI metrics...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.2)' }}>
        <form onSubmit={handleSend} style={{ display: 'flex', gap: '12px', position: 'relative' }}>
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your ingested documents..." 
            style={{ flex: 1, padding: '16px 20px', fontSize: '1rem', background: 'rgba(0,0,0,0.4)' }}
          />
          <button type="submit" className="btn-primary" style={{ padding: '0 24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Send size={18} />
            Send
          </button>
        </form>
      </div>

    </div>
  );
};

export default Query;
