import React, { useState, useRef, useEffect } from 'react';
import { api, type ChatMessage, type ChatResponse } from '../api/client';
import { 
  Send, 
  Bot, 
  User as UserIcon, 
  FileText, 
  AlertTriangle, 
  ShieldAlert,
  Sparkles
} from 'lucide-react';

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'assistant',
      content: 'Welcome to the Federated Agentic Mesh. I am your cross-department multi-agent AI assistant. Queries are automatically routed to Sales, HR, Finance, or Operations agents with strict department boundary enforcement. How can I assist you?',
      timestamp: new Date().toLocaleTimeString(),
      routed_departments: ['orchestrator']
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [targetDept, setTargetDept] = useState<string>('all');
  const [conversationId] = useState<string>(() => `conv-${Date.now()}`);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const resp: ChatResponse = await api.sendChat({
        message: userText,
        conversation_id: conversationId,
        requested_department: targetDept === 'all' ? undefined : targetDept
      });

      const assistantMessage: ChatMessage = {
        id: `resp-${Date.now()}`,
        sender: 'assistant',
        content: resp.answer,
        timestamp: new Date().toLocaleTimeString(),
        routed_departments: resp.routed_departments,
        requires_approval: resp.requires_approval,
        approval_id: resp.approval_id,
        confidence: resp.confidence,
        evidence: resp.evidence
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        content: `Request failed: ${err.message || 'Unable to connect to multi-agent orchestrator.'}`,
        timestamp: new Date().toLocaleTimeString(),
        error: true
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const getDepartmentBadge = (dept: string) => {
    switch (dept.toLowerCase()) {
      case 'sales': return { label: 'Sales Agent', color: '#2563eb', bg: '#eff6ff' };
      case 'hr': return { label: 'HR Agent', color: '#16a34a', bg: '#f0fdf4' };
      case 'finance': return { label: 'Finance Agent', color: '#9333ea', bg: '#faf5ff' };
      case 'operations': return { label: 'Operations Agent', color: '#059669', bg: '#ecfdf5' };
      case 'gateway': return { label: 'Federation Gateway', color: '#d97706', bg: '#fffbeb' };
      default: return { label: `${dept.toUpperCase()} Agent`, color: '#475569', bg: '#f1f5f9' };
    }
  };

  const sampleQueries = [
    "What discount can a sales rep offer before finance approval?",
    "How many days of sick leave are permitted with a medical note?",
    "Which outgoing vendor wire payments require dual authorization?",
    "What is the reorder threshold and safety stock for warehouse inventory items?",
    "Show me the executive salary and equity compensation details."
  ];

  return (
    <div style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Top Controls */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 18px',
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '10px 10px 0 0',
        borderBottom: 'none'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="#2563eb" />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Enterprise Agentic Mesh Chat</span>
          <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>Model: qwen3:8b</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Route Filter:</span>
          <select 
            value={targetDept}
            onChange={(e) => setTargetDept(e.target.value)}
            style={{ width: 'auto', padding: '6px 12px', fontSize: '0.8rem' }}
          >
            <option value="all">Auto Mesh Routing (All 4 Agents)</option>
            <option value="sales">Sales Agent Only</option>
            <option value="hr">HR Agent Only</option>
            <option value="finance">Finance Agent Only</option>
            <option value="operations">Operations Agent Only</option>
          </select>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div style={{
        flex: 1,
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        padding: '24px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}>
        {messages.map((msg) => (
          <div 
            key={msg.id}
            style={{
              display: 'flex',
              gap: '12px',
              maxWidth: '85%',
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row'
            }}
          >
            {/* Avatar */}
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              backgroundColor: msg.sender === 'user' ? '#2563eb' : (msg.error ? '#ef4444' : '#0f172a'),
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              {msg.sender === 'user' ? <UserIcon size={18} /> : (msg.error ? <AlertTriangle size={18} /> : <Bot size={18} />)}
            </div>

            {/* Bubble Content */}
            <div style={{
              backgroundColor: msg.sender === 'user' ? '#2563eb' : '#f8fafc',
              color: msg.sender === 'user' ? '#ffffff' : '#0f172a',
              border: msg.sender === 'user' ? 'none' : '1px solid #e2e8f0',
              borderRadius: '12px',
              padding: '16px 18px',
              fontSize: '0.925rem',
              lineHeight: 1.6
            }}>
              {/* Agent Routing Badges */}
              {msg.routed_departments && msg.routed_departments.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '10px' }}>
                  {msg.routed_departments.map((dept) => {
                    const badge = getDepartmentBadge(dept);
                    return (
                      <span 
                        key={dept} 
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          backgroundColor: badge.bg,
                          color: badge.color,
                          border: `1px solid ${badge.color}40`
                        }}
                      >
                        {badge.label}
                      </span>
                    );
                  })}
                  {msg.confidence !== undefined && (
                    <span style={{ fontSize: '0.7rem', color: '#64748b', alignSelf: 'center' }}>
                      Confidence: {Math.round(msg.confidence * 100)}%
                    </span>
                  )}
                </div>
              )}

              {/* Message Text */}
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </div>

              {/* Sensitive Action Approval Required Notice */}
              {msg.requires_approval && (
                <div style={{
                  marginTop: '14px',
                  padding: '12px 14px',
                  backgroundColor: '#fffbeb',
                  border: '1px solid #fde68a',
                  borderRadius: '6px',
                  color: '#92400e',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <ShieldAlert size={18} style={{ flexShrink: 0 }} />
                  <div>
                    <div style={{ fontWeight: 600 }}>Action Requires Human Authorization</div>
                    <div>This sensitive operation requires manager review before execution. Id: <code>{msg.approval_id}</code></div>
                  </div>
                </div>
              )}

              {/* Grounded Evidence References */}
              {msg.evidence && msg.evidence.length > 0 && (
                <div style={{ marginTop: '14px', borderTop: '1px solid #e2e8f0', paddingTop: '10px' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <FileText size={13} />
                    <span>Grounded Evidence Citations ({msg.evidence.length} retrieved):</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {msg.evidence.map((ev, idx) => (
                      <div 
                        key={idx}
                        style={{
                          backgroundColor: '#ffffff',
                          border: '1px solid #cbd5e1',
                          borderRadius: '6px',
                          padding: '8px 10px',
                          fontSize: '0.8rem'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 600, color: '#1e293b' }}>
                            {ev.title} {ev.page_number ? `(Page ${ev.page_number})` : ''}
                          </span>
                          <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                            Score: {Math.round(ev.confidence * 100)}%
                          </span>
                        </div>
                        <div style={{ color: '#475569', fontStyle: 'italic' }}>
                          "{ev.snippet}"
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ fontSize: '0.7rem', color: msg.sender === 'user' ? '#93c5fd' : '#94a3b8', marginTop: '8px', textAlign: 'right' }}>
                {msg.timestamp}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              backgroundColor: '#0f172a',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Bot size={18} />
            </div>
            <div style={{
              padding: '12px 18px',
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              fontSize: '0.85rem',
              color: '#64748b',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>Orchestrating agents & querying semantic vector index...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div style={{
        backgroundColor: '#ffffff',
        borderLeft: '1px solid #e2e8f0',
        borderRight: '1px solid #e2e8f0',
        padding: '8px 18px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        overflowX: 'auto',
        fontSize: '0.75rem'
      }}>
        <span style={{ color: '#64748b', fontWeight: 600, whiteSpace: 'nowrap' }}>Try prompt:</span>
        {sampleQueries.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setInput(q)}
            style={{
              padding: '4px 10px',
              backgroundColor: '#f1f5f9',
              border: '1px solid #e2e8f0',
              borderRadius: '9999px',
              color: '#334155',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'background 0.15s ease'
            }}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSend} style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '0 0 10px 10px',
        padding: '14px 18px',
        display: 'flex',
        gap: '12px',
        alignItems: 'center'
      }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a cross-department question (e.g. sales discount approvals, medical leave, invoices)..."
          disabled={loading}
          style={{ flex: 1 }}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !input.trim()}
          style={{ padding: '10px 18px', gap: '6px' }}
        >
          <Send size={16} />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
};
