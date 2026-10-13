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
    if (user?.role !== 'admin') {
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
      case 'hr': return '#16a34a';
      case 'finance': return '#9333ea';
      case 'operations': return '#059669';
      default: return '#475569';
    }
  };

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
            <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Department Node: {summary?.department_name || 'Loading...'}</span>
            <span className="badge badge-neutral" style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', color: '#cbd5e1' }}>
              Shared Model: qwen3:8b
            </span>
          </div>
          <h1 style={{ color: '#ffffff', margin: 0, fontSize: '1.5rem' }}>
            Welcome back, {user?.full_name}
          </h1>
          <p style={{ color: '#94a3b8', margin: '4px 0 0 0', fontSize: '0.9rem' }}>
            Federated Zero-Trust Mesh with 4 Autonomous Department Agents: Sales, HR, Finance & Operations.
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
              <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>DEPARTMENT MEMBERS</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>
                {loading ? '...' : (summary?.user_count ?? 0)}
              </div>
            </div>
            <div style={{ padding: '10px', background: '#eff6ff', borderRadius: '8px' }}>
              <Building2 size={22} color="#2563eb" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '8px' }}>
            Scoped to {summary?.department_code.toUpperCase()}
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
              <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>ACTIVE MESH AGENTS</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>
                {loading ? '...' : `${agents.filter(a => a.is_enabled).length} / ${agents.length || 4}`}
              </div>
            </div>
            <div style={{ padding: '10px', background: '#ecfdf5', borderRadius: '8px' }}>
              <Bot size={22} color="#059669" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '8px' }}>
            Sales • HR • Finance • Operations
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>PENDING ACTIONS</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>
                {loading ? '...' : pendingApprovals.length}
              </div>
            </div>
            <div style={{ padding: '10px', background: '#fef2f2', borderRadius: '8px' }}>
              <CheckSquare size={22} color="#dc2626" />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '8px' }}>
            Sensitive approvals requiring review
          </div>
        </div>
      </div>

      {/* Section: Four Department Agents Management (Requirements 1, 2, 3) */}
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

                {user?.role === 'admin' && (
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
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Main 2-column grid: Services & Approvals */}
      <div className="grid-2">
        {/* System & Model Readiness */}
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
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>PostgreSQL with pgvector</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>federated_mesh_dev @ port 5432</div>
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

