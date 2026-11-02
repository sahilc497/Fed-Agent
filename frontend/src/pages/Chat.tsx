import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  api, 
  type ChatMessage, 
  type ChatResponse, 
  type Conversation, 
  type ChatMessageOut,
  type FederationRequestItem
} from '../api/client';
import { 
  Send, 
  Bot, 
  User as UserIcon, 
  FileText, 
  AlertTriangle, 
  ShieldAlert,
  Sparkles,
  Plus,
  MessageSquare,
  Trash2,
  Share2
} from 'lucide-react';

export const Chat: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navState = location.state as {
    conversationId?: string;
    isCrossDeptChat?: boolean;
    targetDepartment?: string;
    grantId?: string;
    approvedFields?: string[];
    expiresAt?: string;
  } | null;

  const isAdmin = user?.role === 'admin';
  const userDeptCode = user?.department_id === 1 ? 'sales' : (user?.department_id === 2 ? 'hr' : (user?.department_id === 3 ? 'finance' : 'operations'));

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeGrants, setActiveGrants] = useState<FederationRequestItem[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [convLoading, setConvLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const getWelcomeMessage = (convTitle?: string): string => {
    if (convTitle && convTitle.toLowerCase().includes('cross dept chat')) {
      const match = convTitle.match(/cross dept chat:\s*([a-zA-Z]+)/i);
      const targetDept = match ? match[1].toUpperCase() : 'CROSS-DEPARTMENT';
      return `Welcome to your dedicated **CROSS Dept Chat** session for **${targetDept}**.\n\nYou have active, approved administrator authorization to query ${targetDept} records under an approved federation grant.\n\n• **Zero-Trust Boundary:** Strictly limited to approved fields; sensitive salaries and financial credentials remain protected.\n• **Persistence:** All questions, answers, and evidence citations in this chat are securely saved in your database history.\n\nWhat would you like to retrieve from ${targetDept}?`;
    }
    if (isAdmin) {
      return 'Welcome to the Federated Agentic Mesh. Administrator multi-department orchestration is active. How can I assist you across the mesh?';
    }
    switch (userDeptCode) {
      case 'sales':
        return 'Welcome to the Sales AI Agent. I can assist you with client opportunities, pipeline BANT criteria, CRM accounts, and proposal discounts. How can I help you today?';
      case 'hr':
        return 'Welcome to the HR AI Agent. I can assist you with employee directories, leave balances, attendance policies, and onboarding procedures. How can I help you today?';
      case 'finance':
        return 'Welcome to the Finance AI Agent. I can assist you with invoices, vendor payables, budgets, and authorized financial policies. How can I help you today?';
      case 'operations':
        return 'Welcome to the Operations AI Agent. I can assist you with warehouse inventory, SKU stock levels, purchase orders, and logistics protocols. How can I help you today?';
      default:
        return 'Welcome to your departmental AI assistant. How can I help you today?';
    }
  };

  const loadActiveGrants = async () => {
    if (isAdmin || !user) return;
    try {
      const allApproved = await api.getFederationRequests('APPROVED');
      const now = new Date();
      const valid = allApproved.filter((g) => {
        if (g.requester_user_id !== user.id) return false;
        if (g.revoked_at) return false;
        if (g.expires_at && new Date(g.expires_at) <= now) return false;
        return true;
      });
      setActiveGrants(valid);
    } catch (err) {
      console.error('Failed to load active federation grants:', err);
    }
  };

  // Load conversations and active federation grants on mount
  useEffect(() => {
    loadConversations();
    loadActiveGrants();
  }, [user]);

  const loadConversations = async () => {
    try {
      const list = await api.getConversations();
      setConversations(list);
      const targetId = navState?.conversationId || (list.length > 0 ? (activeConvId || list[0].id) : '');
      if (targetId) {
        selectConversation(targetId, list);
      } else if (list.length === 0) {
        // Start a default welcome session
        setMessages([
          {
            id: 'welcome-1',
            sender: 'assistant',
            content: getWelcomeMessage(),
            timestamp: new Date().toLocaleTimeString(),
            routed_departments: [isAdmin ? 'orchestrator' : `${userDeptCode}_agent`]
          }
        ]);
      }
    } catch (err: any) {
      console.error('Failed to load conversations:', err);
    }
  };

  const selectConversation = async (convId: string, currentList?: Conversation[]) => {
    setActiveConvId(convId);
    setConvLoading(true);
    const listToSearch = currentList || conversations;
    const foundConv = listToSearch.find((c) => c.id === convId);

    try {
      const dbMsgs: ChatMessageOut[] = await api.getConversationMessages(convId);
      if (dbMsgs.length === 0) {
        setMessages([
          {
            id: `welcome-${convId}`,
            sender: 'assistant',
            content: getWelcomeMessage(foundConv?.title),
            timestamp: new Date().toLocaleTimeString(),
            routed_departments: [isAdmin ? 'orchestrator' : `${userDeptCode}_agent`]
          }
        ]);
      } else {
        const mapped: ChatMessage[] = dbMsgs.map((m) => {
          let evidenceList = m.evidence_json || [];
          if (!evidenceList.length && m.evidence_metadata) {
            try {
              const meta = typeof m.evidence_metadata === 'string' ? JSON.parse(m.evidence_metadata) : m.evidence_metadata;
              if (meta && Array.isArray(meta.evidence)) {
                evidenceList = meta.evidence;
              }
            } catch {
              // ignore
            }
          }
          const text = m.content || m.message || '';
          const timeStr = m.created_at ? new Date(m.created_at).toLocaleTimeString() : new Date().toLocaleTimeString();
          const depts = (m.routed_departments && m.routed_departments.length > 0)
            ? m.routed_departments
            : (m.agent_code ? [m.agent_code] : undefined);

          return {
            id: `msg-${m.id}`,
            sender: m.sender_role === 'user' ? 'user' : 'assistant',
            content: text,
            timestamp: timeStr,
            intent: m.intent,
            routed_departments: depts,
            evidence: evidenceList.length > 0 ? evidenceList : undefined
          };
        });
        setMessages(mapped);
      }
    } catch (err: any) {
      console.error('Failed to load conversation messages:', err);
    } finally {
      setConvLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const deptPrefix = isAdmin ? 'Mesh' : userDeptCode.toUpperCase();
      const newConv = await api.createConversation({
        title: `${deptPrefix} Chat ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
      });
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([
        {
          id: `welcome-${newConv.id}`,
          sender: 'assistant',
          content: getWelcomeMessage(),
          timestamp: new Date().toLocaleTimeString(),
          routed_departments: [isAdmin ? 'orchestrator' : `${userDeptCode}_agent`]
        }
      ]);
    } catch (err: any) {
      alert(`Failed to create conversation: ${err.message}`);
    }
  };

  const handleNewCrossDeptChat = async (grant: FederationRequestItem) => {
    try {
      const targetDept = grant.source_department_code ? grant.source_department_code.toUpperCase() : `DEPT #${grant.source_department_id}`;
      const title = `CROSS Dept Chat: ${targetDept} (#${grant.id.slice(0, 8)})`;
      const newConv = await api.createConversation({ title });
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([
        {
          id: `welcome-${newConv.id}`,
          sender: 'assistant',
          content: getWelcomeMessage(title),
          timestamp: new Date().toLocaleTimeString(),
          routed_departments: [grant.source_department_code ? `${grant.source_department_code}_agent` : 'gateway']
        }
      ]);
    } catch (err: any) {
      alert(`Failed to create CROSS Dept Chat: ${err.message}`);
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this chat session?')) return;
    try {
      await api.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        setActiveConvId('');
        setMessages([]);
      }
    } catch (err: any) {
      alert(`Failed to delete conversation: ${err.message}`);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    // Ensure conversation exists
    let currentConvId = activeConvId;
    if (!currentConvId) {
      try {
        const newConv = await api.createConversation({
          title: userText.slice(0, 32) + (userText.length > 32 ? '...' : '')
        });
        setConversations((prev) => [newConv, ...prev]);
        currentConvId = newConv.id;
        setActiveConvId(newConv.id);
      } catch (err: any) {
        console.error('Failed to auto-create conversation:', err);
      }
    }

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    // Check if the current conversation is a dedicated CROSS Dept Chat
    const activeConv = conversations.find((c) => c.id === currentConvId);
    let targetDeptHint: string | undefined = undefined;
    if (activeConv?.title?.toLowerCase().includes('cross dept chat')) {
      const match = activeConv.title.match(/cross dept chat:\s*([a-zA-Z]+)/i);
      if (match) {
        targetDeptHint = match[1].toLowerCase();
      }
    }

    try {
      // Automatically scope request: Non-admin users are strictly locked to their department agent,
      // with department_hint informing cross-department federated sessions
      const resp: ChatResponse = await api.sendChat({
        message: userText,
        conversation_id: currentConvId || undefined,
        requested_department: isAdmin ? undefined : userDeptCode,
        department_hint: targetDeptHint
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
        content: `Request failed: ${err.message || 'Unable to connect to agent service.'}`,
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
      case 'sales': return { label: 'Sales Agent', color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' };
      case 'hr': return { label: 'HR Agent', color: '#059669', bg: '#ecfdf5', border: '#a7f3d0' };
      case 'finance': return { label: 'Finance Agent', color: '#d97706', bg: '#fffbeb', border: '#fde68a' };
      case 'operations': return { label: 'Operations Agent', color: '#ea580c', bg: '#fff7ed', border: '#fed7aa' };
      case 'admin':
      case 'orchestrator': return { label: 'Executive Admin', color: '#6366f1', bg: '#eef2ff', border: '#c7d2fe' };
      case 'gateway': return { label: 'Federation Gateway', color: '#6366f1', bg: '#eef2ff', border: '#c7d2fe' };
      default: return { label: `${dept.toUpperCase()} Agent`, color: '#475569', bg: '#f1f5f9', border: '#e2e8f0' };
    }
  };

  // Department-specific sample queries
  const getSampleQueries = (): string[] => {
    if (isAdmin) {
      return [
        "What discount can a sales rep offer before finance approval?",
        "How many days of sick leave are permitted with a medical note?",
        "Which outgoing vendor wire payments require dual authorization?",
        "What is the reorder threshold and safety stock for warehouse inventory items?",
        "Show pipeline opportunities currently awaiting finance approval."
      ];
    }
    let baseQueries: string[] = [];
    switch (userDeptCode) {
      case 'sales':
        baseQueries = [
          "What discount can a sales rep offer before finance approval?",
          "What are the BANT qualification criteria for enterprise leads?",
          "List high-probability sales opportunities closing this quarter.",
          "What is our customer onboarding and proposal review procedure?"
        ];
        break;
      case 'hr':
        baseQueries = [
          "How many days of sick leave are permitted with a medical note?",
          "What is the company policy for parental leave and benefits?",
          "What are the employee code of conduct and grievance procedures?",
          "What are the standard onboarding and probationary review steps?"
        ];
        break;
      case 'finance':
        baseQueries = [
          "Which outgoing vendor wire payments require dual authorization?",
          "What is the invoice approval threshold for department managers?",
          "What are the travel and expense reimbursement submission deadlines?",
          "Show pending invoices with Net-30 payment terms."
        ];
        break;
      case 'operations':
        baseQueries = [
          "What is the reorder threshold and safety stock for warehouse inventory items?",
          "What are the warehouse receiving and hazardous storage protocols?",
          "Show purchase orders currently in transit or awaiting delivery.",
          "What is the procedure for reporting equipment maintenance incidents?"
        ];
        break;
      default:
        baseQueries = ["What policies apply to my department?"];
        break;
    }

    // Append authorized cross-department queries if active federation grants exist
    activeGrants.forEach((grant) => {
      const src = grant.source_department_code?.toLowerCase();
      if (src === 'hr') {
        baseQueries.unshift("Show me HR employee details and leave policy (Federated Access)");
      } else if (src === 'finance') {
        baseQueries.unshift("What is the status of invoices and payment due dates? (Federated Access)");
      } else if (src === 'operations') {
        baseQueries.unshift("What are the warehouse inventory stock levels and SKUs? (Federated Access)");
      } else if (src === 'sales') {
        baseQueries.unshift("Show client sales opportunities and deal pipeline (Federated Access)");
      }
    });

    return baseQueries;
  };

  const getPlaceholderText = (): string => {
    if (isAdmin) {
      return "Ask any question across the enterprise mesh (Sales, HR, Finance, Operations)...";
    }
    switch (userDeptCode) {
      case 'sales':
        return "Ask the Sales Agent about opportunities, pipeline BANT, customers, or proposals...";
      case 'hr':
        return "Ask the HR Agent about leave balances, attendance, policies, or benefits...";
      case 'finance':
        return "Ask the Finance Agent about invoices, payables, budgets, or payment thresholds...";
      case 'operations':
        return "Ask the Operations Agent about warehouse stock, SKUs, suppliers, or purchase orders...";
      default:
        return "Type your message to the agent...";
    }
  };

  const sampleQueries = getSampleQueries();
  const activeConv = conversations.find((c) => c.id === activeConvId);
  const isCrossDeptActive = Boolean(activeConv?.title?.toLowerCase().includes('cross dept chat'));
  const crossDeptTarget = isCrossDeptActive 
    ? activeConv?.title?.match(/cross dept chat:\s*([a-zA-Z]+)/i)?.[1]?.toUpperCase() || 'CROSS-DEPARTMENT' 
    : null;

  return (
    <div style={{ height: 'calc(100vh - 120px)', display: 'flex', gap: '16px' }}>
      {/* Left Sidebar: Persistent Chat History */}
      <aside style={{
        width: '260px',
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '10px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        flexShrink: 0
      }}>
        {/* New Chat Button */}
        <div style={{ padding: '12px', borderBottom: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            onClick={handleNewChat}
            className="btn btn-primary"
            style={{ width: '100%', gap: '8px', padding: '10px 14px', fontSize: '0.85rem' }}
          >
            <Plus size={16} />
            <span>New Chat Session</span>
          </button>

          {activeGrants.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {activeGrants.map((grant) => (
                <button
                  key={grant.id}
                  onClick={() => handleNewCrossDeptChat(grant)}
                  className="btn btn-sm"
                  style={{
                    width: '100%',
                    background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                    color: '#ffffff',
                    border: 'none',
                    gap: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    padding: '8px 10px',
                    borderRadius: '6px',
                    boxShadow: '0 1px 3px rgba(99, 102, 241, 0.25)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  title={`Start a new CROSS Dept Chat for ${grant.source_department_code?.toUpperCase()}`}
                >
                  <Share2 size={13} />
                  <span>+ CROSS Dept Chat ({grant.source_department_code?.toUpperCase()})</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Conversation List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', padding: '6px 8px', textTransform: 'uppercase' }}>
            Chat History (SQLite)
          </div>

          {conversations.length === 0 ? (
            <div style={{ padding: '16px 8px', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem' }}>
              No previous chat sessions.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {conversations.map((c) => {
                const isActive = c.id === activeConvId;
                const isCrossDept = c.title.toLowerCase().includes('cross dept chat');
                return (
                  <div
                    key={c.id}
                    onClick={() => selectConversation(c.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 10px',
                      borderRadius: '6px',
                      backgroundColor: isActive ? 'var(--primary-light)' : (isCrossDept ? '#f5f3ff' : 'transparent'),
                      border: isActive 
                        ? '1px solid var(--primary-border)' 
                        : (isCrossDept ? '1px solid #ddd6fe' : '1px solid transparent'),
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      color: isActive ? 'var(--primary)' : (isCrossDept ? '#5b21b6' : '#334155'),
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                      {isCrossDept ? (
                        <Share2 size={14} color={isActive ? 'var(--primary)' : '#7c3aed'} style={{ flexShrink: 0 }} />
                      ) : (
                        <MessageSquare size={14} color={isActive ? 'var(--primary)' : '#94a3b8'} style={{ flexShrink: 0 }} />
                      )}
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: isActive ? 600 : (isCrossDept ? 600 : 400) }}>
                        {c.title}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      {isCrossDept && (
                        <span style={{
                          fontSize: '0.62rem',
                          padding: '1px 4px',
                          borderRadius: '4px',
                          backgroundColor: '#ede9fe',
                          color: '#6d28d9',
                          fontWeight: 700,
                          flexShrink: 0
                        }}>
                          CROSS
                        </span>
                      )}
                      <button
                        onClick={(e) => handleDeleteConversation(e, c.id)}
                        title="Delete chat"
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          color: '#94a3b8',
                          padding: '2px 4px',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </aside>

      {/* Main Chat Panel */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Chat Top Header - Clean, Scoped & Zero-Trust Protected */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 20px',
          backgroundColor: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '10px 10px 0 0',
          borderBottom: 'none'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {isCrossDeptActive ? (
              <>
                <div style={{
                  width: 28,
                  height: 28,
                  borderRadius: 6,
                  background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <Share2 size={16} color="#ffffff" />
                </div>
                <div>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#4338ca' }}>
                    CROSS Dept Chat • {crossDeptTarget}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: '#6d28d9', marginLeft: '8px' }}>
                    (Federated Approved Grant Session)
                  </span>
                </div>
              </>
            ) : (
              <>
                <Sparkles size={18} color="var(--primary)" />
                <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#0f172a' }}>
                  {isAdmin ? 'Enterprise Agentic Mesh Chat' : `${userDeptCode.toUpperCase()} AI Agent`}
                </span>
                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                  {isAdmin ? '• Multi-Department Orchestration' : `• Scoped to ${userDeptCode.toUpperCase()}`}
                </span>
              </>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {isCrossDeptActive ? (
              <span className="badge" style={{ backgroundColor: '#ede9fe', color: '#6d28d9', border: '1px solid #ddd6fe', fontSize: '0.75rem', fontWeight: 600 }}>
                CROSS DEPT SCOPE
              </span>
            ) : (
              <span className="badge badge-primary" style={{ fontSize: '0.75rem' }}>
                {isAdmin ? 'All Departments Scope' : `${userDeptCode.toUpperCase()} Agent Active`}
              </span>
            )}
            <span className="badge badge-success" style={{ fontSize: '0.75rem' }}>
              Zero-Trust Protected
            </span>
          </div>
        </div>

        {/* Active Federation Grants Banner */}
        {activeGrants.length > 0 && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderBottom: 'none',
            padding: '10px 20px'
          }}>
            {activeGrants.map((grant) => (
              <div key={grant.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem', color: '#166534' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Share2 size={15} color="#16a34a" />
                  <span>
                    <strong>Active Federation Grant:</strong> Authorized cross-department access to <strong>{grant.source_department_code?.toUpperCase()}</strong> until <strong>{grant.expires_at ? new Date(grant.expires_at).toLocaleTimeString() : 'Expiry'}</strong> (Grant #{grant.id.slice(0, 8)}).
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                    Released Fields: {grant.approved_fields?.join(', ') || 'Standard Scope'}
                  </span>
                  <button
                    type="button"
                    className="btn btn-sm"
                    onClick={() => handleNewCrossDeptChat(grant)}
                    style={{
                      backgroundColor: '#15803d',
                      color: '#ffffff',
                      border: 'none',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      padding: '3px 8px',
                      borderRadius: '5px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                    title={`Start a new CROSS Dept Chat session for ${grant.source_department_code?.toUpperCase()}`}
                  >
                    <MessageSquare size={12} />
                    <span>Open CROSS Dept Chat</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

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
          {convLoading ? (
            <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
              Loading conversation history from SQLite...
            </div>
          ) : (
            messages.map((msg) => (
              <div 
                key={msg.id}
                style={{
                  display: 'flex',
                  gap: '12px',
                  maxWidth: '85%',
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                {msg.sender === 'assistant' && (
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    backgroundColor: msg.error ? '#fee2e2' : '#eff6ff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    {msg.error ? (
                      <AlertTriangle size={18} color="#ef4444" />
                    ) : (
                      <Bot size={18} color="#2563eb" />
                    )}
                  </div>
                )}

                <div>
                  {/* Routed Agent Badge */}
                  {msg.sender === 'assistant' && msg.routed_departments && msg.routed_departments.length > 0 && (
                    <div style={{ display: 'flex', gap: '6px', marginBottom: '6px' }}>
                      {msg.routed_departments.map((dept, idx) => {
                        const badge = getDepartmentBadge(dept.replace('_agent', ''));
                        return (
                          <span 
                            key={idx}
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 600,
                              color: badge.color,
                              backgroundColor: badge.bg,
                              padding: '2px 8px',
                              borderRadius: '4px',
                              border: `1px solid ${badge.color}20`
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

                  {/* Message Bubble */}
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: msg.sender === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                    backgroundColor: msg.sender === 'user' ? '#2563eb' : (msg.error ? '#fef2f2' : '#f8fafc'),
                    color: msg.sender === 'user' ? '#ffffff' : (msg.error ? '#991b1b' : '#0f172a'),
                    border: msg.sender === 'user' ? 'none' : '1px solid #e2e8f0',
                    lineHeight: '1.5',
                    fontSize: '0.9rem',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                  }}>
                    {msg.content}
                  </div>

                  {/* Grounded Evidence Citations */}
                  {msg.evidence && msg.evidence.length > 0 && (
                    <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <FileText size={12} />
                        <span>Grounded Evidence Citations ({msg.evidence.length} sources):</span>
                      </span>
                      {msg.evidence.map((ev, i) => (
                        <div 
                          key={i} 
                          style={{
                            fontSize: '0.75rem',
                            padding: '8px 12px',
                            backgroundColor: '#f1f5f9',
                            borderRadius: '6px',
                            borderLeft: '3px solid #2563eb'
                          }}
                        >
                          <div style={{ fontWeight: 600, color: '#1e293b', marginBottom: '2px' }}>
                            {ev.title} {ev.page_number && `(Page ${ev.page_number})`}
                          </div>
                          <div style={{ color: '#475569', fontStyle: 'italic', marginBottom: '4px' }}>
                            "{ev.snippet}"
                          </div>
                          <div style={{ display: 'flex', gap: '10px', fontSize: '0.7rem', color: '#64748b' }}>
                            <span>Dept: <strong style={{ textTransform: 'uppercase' }}>{ev.department}</strong></span>
                            <span>Score: {ev.confidence ? Math.round(ev.confidence * 100) : 0}%</span>
                            <span>Doc ID: #{ev.document_id}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Federation / Action Approval Notification */}
                  {msg.requires_approval && (
                    <div style={{
                      marginTop: '8px',
                      padding: '8px 12px',
                      backgroundColor: '#fffbeb',
                      border: '1px solid #fef3c7',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '0.8rem',
                      color: '#92400e'
                    }}>
                      <ShieldAlert size={16} color="#d97706" />
                      <div>
                        This sensitive cross-department action requires <strong>Administrator Approval</strong>. Request #{msg.approval_id || 'PENDING'} recorded.
                      </div>
                    </div>
                  )}

                  <div style={{
                    fontSize: '0.7rem',
                    color: '#94a3b8',
                    marginTop: '4px',
                    textAlign: msg.sender === 'user' ? 'right' : 'left'
                  }}>
                    {msg.timestamp}
                  </div>
                </div>

                {msg.sender === 'user' && (
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    backgroundColor: '#e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <UserIcon size={18} color="#475569" />
                  </div>
                )}
              </div>
            ))
          )}

          {loading && (
            <div style={{ display: 'flex', gap: '12px', alignSelf: 'flex-start', maxWidth: '80%' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: '#eff6ff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Bot size={18} color="#2563eb" />
              </div>
              <div style={{
                padding: '12px 16px',
                borderRadius: '12px 12px 12px 0',
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                color: '#64748b',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div className="spinner" style={{ width: '14px', height: '14px' }} />
                <span>Generating grounded answer with local qwen3:8b model...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips - Scoped to User's Department */}
        <div style={{
          backgroundColor: '#ffffff',
          borderLeft: '1px solid #e2e8f0',
          borderRight: '1px solid #e2e8f0',
          padding: '10px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          overflowX: 'auto',
          fontSize: '0.8rem'
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
            placeholder={getPlaceholderText()}
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
    </div>
  );
};
