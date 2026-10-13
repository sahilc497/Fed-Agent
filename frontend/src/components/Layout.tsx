import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api, type HealthReadyStatus } from '../api/client';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Building2, 
  FileText, 
  CheckSquare, 
  ShieldAlert, 
  Users, 
  LogOut,
  Activity,
  Server
} from 'lucide-react';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthReadyStatus | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        const h = await api.getHealthReady();
        if (isMounted) setHealth(h);
      } catch {
        if (isMounted) setHealth(null);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 20000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getRoleBadgeClass = (role?: string) => {
    switch (role) {
      case 'admin': return 'badge-danger';
      case 'auditor': return 'badge-warning';
      case 'department_manager': return 'badge-primary';
      default: return 'badge-neutral';
    }
  };

  const formatRole = (role?: string) => {
    switch (role) {
      case 'admin': return 'Administrator';
      case 'auditor': return 'Security Auditor';
      case 'department_manager': return 'Dept Manager';
      case 'department_employee': return 'Staff Employee';
      default: return role || '';
    }
  };

  const isReady = health?.status === 'ready';

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Server size={24} color="#3b82f6" />
          <div>
            <div className="sidebar-title">Agentic Mesh</div>
            <div className="sidebar-subtitle">Federated Enterprise AI</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </NavLink>

          <NavLink to="/chat" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <MessageSquare size={18} />
            <span>AI Mesh Chat</span>
          </NavLink>

          <NavLink to="/departments" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Building2 size={18} />
            <span>Department Records</span>
          </NavLink>

          <NavLink to="/documents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <FileText size={18} />
            <span>Knowledge Docs</span>
          </NavLink>

          <NavLink to="/approvals" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <CheckSquare size={18} />
            <span>Approvals</span>
          </NavLink>

          <NavLink to="/audit" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <ShieldAlert size={18} />
            <span>Audit Trail</span>
          </NavLink>

          {user && (user.role === 'admin' || user.role === 'auditor') && (
            <NavLink to="/admin/users" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Users size={18} />
              <span>User Admin</span>
            </NavLink>
          )}
        </nav>

        {/* Sidebar Footer with Health & Profile */}
        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: '#94a3b8' }}>
              <Activity size={14} color={isReady ? '#10b981' : '#f59e0b'} />
              <span>Mesh Service:</span>
            </div>
            <span className={`badge ${isReady ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.7rem' }}>
              {isReady ? 'Active' : 'Checking'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {user?.full_name}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {user?.email}
              </div>
            </div>
            <button 
              onClick={handleLogout} 
              className="btn btn-secondary btn-sm" 
              title="Sign out"
              style={{ padding: '6px 8px', background: 'transparent', borderColor: '#334155', color: '#cbd5e1' }}
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-content">
        <header className="top-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500, color: '#64748b' }}>Enterprise Scope:</span>
            <span className="badge badge-primary">Dept ID: {user?.department_id}</span>
            <span className={`badge ${getRoleBadgeClass(user?.role)}`}>
              {formatRole(user?.role)}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Zero-Trust Isolation • Semantic RAG
            </div>
          </div>
        </header>

        <main className="page-body">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
