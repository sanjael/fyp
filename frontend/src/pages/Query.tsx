import React, { useState, useRef, useEffect } from 'react';
import { Send, ShieldAlert, CheckCircle, AlertTriangle, FileText } from 'lucide-react';
import axios from 'axios';

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

// Import missing icon at the top
import { MessageSquareText } from 'lucide-react';

export default Query;
