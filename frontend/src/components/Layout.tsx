import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
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
  Server,
  UserCircle,
  Palette,
  RotateCcw
} from 'lucide-react';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, themeMeta, setTheme, isCustomPreview, resetToUserDefault, availableThemes } = useTheme();
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
      case 'department_manager': return 'badge-primary';
      default: return 'badge-neutral';
    }
  };

  const formatRole = (role?: string) => {
    switch (role) {
      case 'admin': return 'Administrator';
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
          <div style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: 'var(--theme-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--theme-glow)',
            flexShrink: 0
          }}>
            <Server size={20} color="#ffffff" />
          </div>
          <div>
            <div className="sidebar-title">Agentic Mesh</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
              <span className="sidebar-subtitle">Federated Enterprise AI</span>
              <span style={{
                fontSize: '0.65rem',
                padding: '1px 5px',
                borderRadius: 4,
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                color: themeMeta.primaryColor,
                fontWeight: 700,
                letterSpacing: '0.04em',
                textTransform: 'uppercase'
              }}>
                {themeMeta.name.split(' ')[0]}
              </span>
            </div>
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

          {user && (user.role === 'admin' || user.role === 'department_manager') && (
            <NavLink to="/audit" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <ShieldAlert size={18} />
              <span>Audit Trail</span>
            </NavLink>
          )}

          {user && user.role === 'admin' && (
            <NavLink to="/admin/users" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Users size={18} />
              <span>User Admin</span>
            </NavLink>
          )}

          <NavLink to="/profile" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <UserCircle size={18} />
            <span>My Profile</span>
          </NavLink>
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
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Mesh Scope:</span>
            <span className={`badge badge-theme-${theme}`}>
              Dept ID: {user?.department_id}
            </span>
            <span className={`badge ${getRoleBadgeClass(user?.role)}`}>
              {formatRole(user?.role)}
            </span>
            <span 
              className={`badge badge-theme-${theme}`} 
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 700 }}
              title={themeMeta.description}
            >
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: themeMeta.primaryColor, display: 'inline-block' }}></span>
              {themeMeta.name}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* Admin Department Theme Switcher / Preview */}
            {user?.role === 'admin' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#f8fafc', padding: '3px 8px', borderRadius: 20, border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Palette size={13} color="var(--primary)" /> Dept Theme:
                </span>
                {availableThemes.map((t) => {
                  const isActive = theme === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setTheme(t.id)}
                      className={`theme-pill-btn ${isActive ? 'active' : ''}`}
                      style={{
                        background: isActive ? t.accentGradient : undefined,
                        color: isActive ? '#ffffff' : undefined,
                        borderColor: isActive ? 'transparent' : undefined,
                        fontSize: '0.72rem',
                        padding: '3px 8px'
                      }}
                      title={`Preview UI styled as ${t.name} (${t.badgeLabel})`}
                    >
                      <span 
                        style={{ 
                          width: 6, 
                          height: 6, 
                          borderRadius: '50%', 
                          background: isActive ? '#ffffff' : t.primaryColor,
                          display: 'inline-block'
                        }} 
                      />
                      {t.id.toUpperCase()}
                    </button>
                  );
                })}
                {isCustomPreview && (
                  <button
                    onClick={resetToUserDefault}
                    className="btn btn-secondary btn-sm"
                    style={{ padding: '2px 6px', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 3 }}
                    title="Reset to default Admin theme"
                  >
                    <RotateCcw size={11} /> Reset
                  </button>
                )}
              </div>
            )}

            <div style={{ fontSize: '0.8rem', color: '#64748b', whiteSpace: 'nowrap' }}>
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
