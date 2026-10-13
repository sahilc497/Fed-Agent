import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Server, Lock, Mail, ShieldCheck, AlertCircle } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('Please provide both corporate email and password.');
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('MeshSecure2026!');
  };

  const demoAccounts = [
    { role: 'Admin (Full Mesh)', email: 'admin@mesh.enterprise.internal', dept: 'Finance/Admin' },
    { role: 'Sales Manager', email: 'sales.manager@mesh.enterprise.internal', dept: 'Sales' },
    { role: 'Sales Representative', email: 'sales.rep@mesh.enterprise.internal', dept: 'Sales' },
    { role: 'HR Director', email: 'hr.manager@mesh.enterprise.internal', dept: 'HR' },
    { role: 'HR Specialist', email: 'hr.specialist@mesh.enterprise.internal', dept: 'HR' },
    { role: 'Finance Controller', email: 'finance.manager@mesh.enterprise.internal', dept: 'Finance' },
    { role: 'Finance Analyst', email: 'finance.analyst@mesh.enterprise.internal', dept: 'Finance' },
    { role: 'Security Auditor', email: 'auditor@mesh.enterprise.internal', dept: 'Compliance' },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#0f172a',
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '460px',
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          backgroundColor: '#1e293b',
          color: '#ffffff',
          padding: '28px 24px',
          textAlign: 'center'
        }}>
          <div style={{
            display: 'inline-flex',
            padding: '10px',
            borderRadius: '12px',
            backgroundColor: 'rgba(59, 130, 246, 0.15)',
            marginBottom: '12px'
          }}>
            <Server size={32} color="#3b82f6" />
          </div>
          <h1 style={{ color: '#ffffff', fontSize: '1.4rem', fontWeight: 700, margin: 0 }}>
            Federated Agentic Mesh
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '6px' }}>
            Zero-Trust Multi-Agent Enterprise Intelligence
          </p>
        </div>

        {/* Form Body */}
        <div style={{ padding: '28px 24px' }}>
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              padding: '12px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              marginBottom: '20px'
            }}>
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Corporate Email Address</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@mesh.enterprise.internal"
                  required
                  style={{ paddingLeft: '36px' }}
                />
                <Mail size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '24px' }}>
              <label htmlFor="password">Security Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  style={{ paddingLeft: '36px' }}
                />
                <Lock size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', padding: '12px', fontSize: '0.95rem' }}
            >
              {loading ? 'Authenticating & Verifying...' : 'Authenticate & Sign In'}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8rem',
              fontWeight: 600,
              color: '#475569',
              marginBottom: '12px'
            }}>
              <ShieldCheck size={16} color="#2563eb" />
              <span>Quick Demo Personas (Pre-seeded):</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              {demoAccounts.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => handleQuickSelect(acc.email)}
                  style={{
                    textAlign: 'left',
                    padding: '8px 10px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    backgroundColor: email === acc.email ? '#eff6ff' : '#f8fafc',
                    borderColor: email === acc.email ? '#3b82f6' : '#e2e8f0',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ fontWeight: 600, color: '#1e293b' }}>{acc.role}</div>
                  <div style={{ color: '#64748b', fontSize: '0.7rem' }}>{acc.dept}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
