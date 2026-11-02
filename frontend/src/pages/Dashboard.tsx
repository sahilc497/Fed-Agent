import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  api, 
  type DepartmentSummary, 
  type ApprovalRequestItem, 
  type HealthReadyStatus,
  type DepartmentAgentItem
} from '../api/client';
import { 
  Building2, 
  FileText, 
  CheckSquare, 
  Bot, 
  Database, 
  Cpu, 
  ArrowRight,
  ShieldCheck,
  Clock,
  Power,
  Share2
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [summary, setSummary] = useState<DepartmentSummary | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalRequestItem[]>([]);
  const [health, setHealth] = useState<HealthReadyStatus | null>(null);
  const [agents, setAgents] = useState<DepartmentAgentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [agentActionLoading, setAgentActionLoading] = useState<number | null>(null);

  const loadDashboardData = async () => {
    try {
      const [sumRes, apprRes, healthRes, agentsRes] = await Promise.allSettled([
        api.getMyDepartmentSummary(),
        api.getApprovals('pending'),
        api.getHealthReady(),
        api.getAgents()
      ]);

      if (sumRes.status === 'fulfilled') setSummary(sumRes.value);
      if (apprRes.status === 'fulfilled') setPendingApprovals(apprRes.value);
      if (healthRes.status === 'fulfilled') setHealth(healthRes.value);
      if (agentsRes.status === 'fulfilled') setAgents(agentsRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleToggleAgent = async (agent: DepartmentAgentItem) => {
    if (!isAdmin) {
      alert('Only administrators can enable or disable department agents.');
      return;
    }
    setAgentActionLoading(agent.id);
    try {
      await api.toggleAgent(agent.agent_code, !agent.is_enabled);
      await loadDashboardData();
    } catch (err: any) {
      alert(`Failed to update agent: ${err.message}`);
    } finally {
      setAgentActionLoading(null);
    }
  };

  const getDeptColor = (code: string) => {
    switch (code.toLowerCase()) {
      case 'sales': return '#2563eb';
      case 'hr': return '#059669';
      case 'finance': return '#d97706';
      case 'operations': return '#ea580c';
      case 'admin': return '#6366f1';
      default: return '#475569';
    }
  };

  const myAgent = agents.find(a => a.department_id === user?.department_id) || (
    user?.department_id === 1 ? { id: 1, department_id: 1, agent_code: 'sales_agent', name: 'Sales Agent', description: 'Handles client proposals, discounts & pipeline CRM inquiries.', is_enabled: true, error_count: 0 } :
    user?.department_id === 2 ? { id: 2, department_id: 2, agent_code: 'hr_agent', name: 'HR Agent', description: 'Handles leave balances, benefits & department staffing.', is_enabled: true, error_count: 0 } :
    user?.department_id === 3 ? { id: 3, department_id: 3, agent_code: 'finance_agent', name: 'Finance Agent', description: 'Handles invoices, budget tracking & dual-authorized wires.', is_enabled: true, error_count: 0 } :
    { id: 4, department_id: 4, agent_code: 'operations_agent', name: 'Operations Agent', description: 'Handles inventory, warehouse stock, fulfillment & supply logistics.', is_enabled: true, error_count: 0 }
  );

  return (
    <div>
      {/* Welcome Banner */}
      <div style={{
        background: 'linear-gradient(to right, #1e293b, #0f172a)',
        color: '#ffffff',
        borderRadius: '12px',
        padding: '24px 28px',
        marginBottom: '28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="badge badge-primary">Active Enterprise Mesh</span>
            <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              {isAdmin ? 'Global Administration Console' : `Department Node: ${summary?.department_name || 'Loading...'}`}
            </span>
            {isAdmin && (
              <span className="badge badge-neutral" style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', color: '#cbd5e1' }}>
                Shared Model: qwen3:8b
              </span>
            )}
          </div>
          <h1 style={{ color: '#ffffff', margin: 0, fontSize: '1.5rem' }}>
            Welcome back, {user?.full_name}
          </h1>
          <p style={{ color: '#94a3b8', margin: '4px 0 0 0', fontSize: '0.9rem' }}>
            {isAdmin 
              ? 'Federated Zero-Trust Mesh with 4 Autonomous Department Agents: Sales, HR, Finance & Operations.'
              : `Scoped strictly to ${summary?.department_name || 'your department'}. Zero-trust data isolation enforced.`}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to="/approvals" className="btn btn-secondary" style={{ padding: '10px 16px', gap: '8px', background: 'rgba(255,255,255,0.1)', color: '#ffffff', borderColor: 'transparent' }}>
            <Share2 size={16} />
            <span>Federation Requests</span>
          </Link>
          <Link to="/chat" className="btn btn-primary" style={{ padding: '10px 20px', gap: '8px' }}>
            <Bot size={18} />
            <span>Open AI Mesh Chat</span>
          </Link>
        </div>
      </div>

      {/* Primary Metrics Row */}
      <div className="grid-4" style={{ marginBottom: '28px' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
                {isAdmin ? 'DEPARTMENT MEMBERS' : 'MY DEPARTMENT'}
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>
                {loading ? '...' : (isAdmin ? (summary?.user_count ?? 0) : (summary?.department_code?.toUpperCase() || 'DEPT'))}
              </div>
            </div>
            <div style={{ padding: '10px', background: '#eff6ff', borderRadius: '8px' }}>
              <Building2 size={22} color="#2563eb" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '8px' }}>
            {isAdmin ? `Scoped to ${summary?.department_code?.toUpperCase() || 'ALL'}` : (summary?.department_name || 'Assigned Department')}
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>AUTHORIZED DOCUMENTS</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>
                {loading ? '...' : (summary?.authorized_document_count ?? 0)}
              </div>
            </div>
            <div style={{ padding: '10px', background: '#f0fdf4', borderRadius: '8px' }}>
              <FileText size={22} color="#16a34a" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '8px' }}>
            RAG Indexed with all-MiniLM-L6-v2
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
                {isAdmin ? 'ACTIVE MESH AGENTS' : 'ASSIGNED AGENT'}
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>
                {loading ? '...' : (isAdmin ? `${agents.filter(a => a.is_enabled).length} / ${agents.length || 4}` : (myAgent?.name || 'Assigned Agent'))}
              </div>
            </div>
            <div style={{ padding: '10px', background: '#ecfdf5', borderRadius: '8px' }}>
              <Bot size={22} color="#059669" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '8px' }}>
            {isAdmin ? 'Sales • HR • Finance • Operations' : (myAgent?.is_enabled ? 'Active • Ready for Tasks' : 'Disabled by Administrator')}
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
                {isAdmin ? 'PENDING ACTIONS' : 'PENDING APPROVALS'}
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>
                {loading ? '...' : pendingApprovals.length}
              </div>
            </div>
            <div style={{ padding: '10px', background: '#fef2f2', borderRadius: '8px' }}>
              <CheckSquare size={22} color="#dc2626" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '8px' }}>
            {isAdmin ? 'Sensitive approvals requiring review' : 'Federation & action review'}
          </div>
        </div>
      </div>

      {/* SECTION: ADMIN ONLY - Four Department Agents Management */}
      {isAdmin ? (
        <div className="card" style={{ marginBottom: '28px' }}>
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem' }}>Four Department Mesh Agents (Shared Local Ollama)</h2>
              <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                All 4 agents share a single local <code>qwen3:8b</code> deployment. Administrator toggling enables or disables agent task dispatch.
              </p>
            </div>
            <span className="badge badge-success" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Cpu size={14} />
              <span>Shared Model: qwen3:8b</span>
            </span>
          </div>

          <div className="grid-4">
            {(agents.length > 0 ? agents : [
              { id: 1, department_id: 1, agent_code: 'sales_agent', name: 'Sales Agent', description: 'Handles client proposals, discounts & pipeline CRM inquiries.', is_enabled: true, error_count: 0 },
              { id: 2, department_id: 2, agent_code: 'hr_agent', name: 'HR Agent', description: 'Handles leave balances, benefits & department staffing.', is_enabled: true, error_count: 0 },
              { id: 3, department_id: 3, agent_code: 'finance_agent', name: 'Finance Agent', description: 'Handles invoices, budget tracking & dual-authorized wires.', is_enabled: true, error_count: 0 },
              { id: 4, department_id: 4, agent_code: 'operations_agent', name: 'Operations Agent', description: 'Handles inventory, warehouse stock, fulfillment & supply logistics.', is_enabled: true, error_count: 0 }
            ]).map((agent: any) => {
              const deptCode = agent.agent_code.replace('_agent', '');
              const color = getDeptColor(deptCode);

              return (
                <div 
                  key={agent.id} 
                  style={{
                    border: `1px solid ${agent.is_enabled ? '#e2e8f0' : '#fecaca'}`,
                    borderRadius: '10px',
                    padding: '16px',
                    backgroundColor: agent.is_enabled ? '#ffffff' : '#fff5f5',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    boxShadow: 'var(--shadow-sm)'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: color }} />
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>{agent.name}</span>
                      </div>
                      <span className={`badge ${agent.is_enabled ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.7rem' }}>
                        {agent.is_enabled ? 'Active' : 'Disabled'}
                      </span>
                    </div>

                    <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0 0 12px 0', minHeight: '38px', lineHeight: '1.3' }}>
                      {agent.description}
                    </p>

                    <div style={{ background: '#f8fafc', padding: '8px 10px', borderRadius: '6px', fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                        <span>Department:</span>
                        <strong style={{ color: color, textTransform: 'uppercase' }}>{deptCode}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                        <span>Shared Engine:</span>
                        <span>qwen3:8b</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                        <span>Error Count:</span>
                        <span style={{ color: agent.error_count > 0 ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                          {agent.error_count}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid #e2e8f0' }}>
                    <button
                      type="button"
                      className={`btn btn-sm ${agent.is_enabled ? 'btn-secondary' : 'btn-primary'}`}
                      style={{ width: '100%', gap: '6px', justifyContent: 'center' }}
                      onClick={() => handleToggleAgent(agent)}
                      disabled={agentActionLoading === agent.id}
                    >
                      <Power size={13} />
                      <span>{agent.is_enabled ? 'Disable Agent' : 'Enable Agent'}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* SECTION: NON-ADMIN VIEW - Only Show User's Own Department Agent */
        <div className="card" style={{ marginBottom: '28px' }}>
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem' }}>
                Your Assigned Department Agent: {myAgent?.name || 'Department Agent'}
              </h2>
              <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                Autonomous agent scoped strictly to {summary?.department_name || 'your department'} knowledge and records.
              </p>
            </div>
            <span className={`badge ${myAgent?.is_enabled ? 'badge-success' : 'badge-danger'}`} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Bot size={14} />
              <span>{myAgent?.is_enabled ? 'Agent Active' : 'Agent Disabled by Admin'}</span>
            </span>
          </div>

          <div style={{
            padding: '20px',
            background: '#f8fafc',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px'
          }}>
            <div style={{ maxWidth: '650px' }}>
              <div style={{ fontWeight: 600, color: '#1e293b', fontSize: '0.95rem', marginBottom: '6px' }}>
                {myAgent?.description}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                Scope: <strong>{summary?.department_name || 'Assigned Department'}</strong> • Zero-Trust Data Isolation: <strong>Enforced</strong>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <Link to="/chat" className="btn btn-primary" style={{ gap: '8px' }}>
                <Bot size={16} />
                <span>Chat with {myAgent?.name || 'Agent'}</span>
              </Link>
              <Link to="/departments" className="btn btn-secondary" style={{ gap: '8px' }}>
                <Building2 size={16} />
                <span>View Department Records</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Main 2-column grid: Services & Approvals */}
      <div className="grid-2">
        {isAdmin ? (
          /* System & Model Readiness - ADMIN ONLY */
          <div className="card">
            <div className="card-header">
              <h2>Federated Mesh Infrastructure Status</h2>
              <span className={`badge ${health?.status === 'ready' ? 'badge-success' : 'badge-warning'}`}>
                {health?.status === 'ready' ? 'Operational' : 'Verifying'}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: '#f8fafc', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Database size={18} color="#2563eb" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>SQLite3 (Standard-Library, WAL Mode)</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>backend/data/federated_mesh.db</div>
                  </div>
                </div>
                <span className="badge badge-success">
                  {health?.dependencies.database.status === 'connected' ? 'Connected' : 'Active'}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: '#f8fafc', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Cpu size={18} color="#9333ea" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Shared Answer LLM: qwen3:8b</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Local Ollama Runtime @ port 11434 (All 4 Agents)</div>
                  </div>
                </div>
                <span className="badge badge-success">
                  {health?.dependencies.ollama_local_runtime.available ? 'Ready' : 'Connected'}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: '#f8fafc', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <ShieldCheck size={18} color="#059669" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Semantic Embedding Engine</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>sentence-transformers/all-MiniLM-L6-v2 (384-dim)</div>
                  </div>
                </div>
                <span className="badge badge-success">Verified Offline</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: '#f8fafc', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Share2 size={18} color="#d97706" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Federation Gateway & Access Requests</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Admin-governed cross-department data federation</div>
                  </div>
                </div>
                <span className="badge badge-success">Enforced</span>
              </div>
            </div>
          </div>
        ) : (
          /* Department Workspace & Data Scope - NON-ADMIN VIEW */
          <div className="card">
            <div className="card-header">
              <h2>Department Workspace & Scope</h2>
              <span className="badge badge-primary">Dept ID: {user?.department_id}</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', background: '#f8fafc', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <ShieldCheck size={20} color="#16a34a" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Zero-Trust Data Isolation</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      Access restricted strictly to {summary?.department_name || 'your department'} records
                    </div>
                  </div>
                </div>
                <span className="badge badge-success">Enforced</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', background: '#f8fafc', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <FileText size={20} color="#2563eb" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Authorized Knowledge Base</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      {summary?.authorized_document_count ?? 0} indexed policies & procedures
                    </div>
                  </div>
                </div>
                <Link to="/documents" style={{ fontSize: '0.8rem', color: '#2563eb', fontWeight: 600 }}>
                  Browse Docs
                </Link>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', background: '#f8fafc', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Share2 size={20} color="#d97706" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Cross-Department Federation</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      Request access to other departments via Federation Gateway
                    </div>
                  </div>
                </div>
                <Link to="/approvals" style={{ fontSize: '0.8rem', color: '#d97706', fontWeight: 600 }}>
                  Create Request
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Pending Approvals Widget */}
        <div className="card">
          <div className="card-header">
            <h2>Pending Action Approvals</h2>
            <Link to="/approvals" style={{ fontSize: '0.85rem', color: '#2563eb', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>View Approvals & Federation</span>
              <ArrowRight size={14} />
            </Link>
          </div>

          {pendingApprovals.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px 20px', color: '#64748b' }}>
              <CheckSquare size={32} color="#94a3b8" style={{ margin: '0 auto 12px auto' }} />
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>No pending approvals</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>All sensitive actions and federation requests have been reviewed.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {pendingApprovals.slice(0, 3).map((appr) => (
                <div key={appr.id} style={{
                  padding: '12px 14px',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  backgroundColor: '#ffffff'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b' }}>
                      {appr.action_type.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="badge badge-warning">Pending Review</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#475569' }}>
                    Operation: <code>{appr.requested_operation}</code> on <code>{appr.target_resource}</code>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    <span>Requested: {new Date(appr.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
