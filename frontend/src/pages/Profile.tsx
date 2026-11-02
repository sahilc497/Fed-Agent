import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { Shield, Building, Mail, CheckCircle2, AlertCircle, Save } from 'lucide-react';

export const Profile: React.FC = () => {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const updated = await api.updateProfile({
        full_name: fullName.trim(),
        bio: bio.trim()
      });
      setSuccessMsg('Your user profile has been updated successfully.');
      // Update local storage representation
      localStorage.setItem('mesh_user', JSON.stringify(updated));
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update user profile.');
    } finally {
      setLoading(false);
    }
  };

  const getRoleName = (role?: string) => {
    switch (role) {
      case 'admin': return 'Administrator (Full Mesh Operations)';
      case 'department_manager': return 'Department Manager (Authorized Approvals)';
      case 'department_employee': return 'Staff Employee (Department Scoped)';
      default: return role || 'User';
    }
  };

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', padding: '12px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a' }}>My Enterprise Profile</h1>
        <p className="subtitle">
          Manage your enterprise identity, display preferences, and view backend-enforced RBAC privileges.
        </p>
      </div>

      {successMsg && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backgroundColor: '#f0fdf4',
          border: '1px solid #bbf7d0',
          color: '#166534',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
          fontSize: '0.9rem'
        }}>
          <CheckCircle2 size={18} />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          color: '#991b1b',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
          fontSize: '0.9rem'
        }}>
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
      }}>
        {/* Read-Only RBAC Metadata */}
        <div style={{
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '8px',
          padding: '16px 20px',
          marginBottom: '24px'
        }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '12px' }}>
            Security Scope & Department Boundaries (Backend Enforced)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
              <Shield size={16} color="#2563eb" />
              <div>
                <span style={{ color: '#64748b' }}>Role: </span>
                <span style={{ fontWeight: 600, color: '#1e293b' }}>{getRoleName(user?.role)}</span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
              <Building size={16} color="#059669" />
              <div>
                <span style={{ color: '#64748b' }}>Department: </span>
                <span style={{ fontWeight: 600, color: '#1e293b' }}>Department #{user?.department_id}</span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
              <Mail size={16} color="#d97706" />
              <div>
                <span style={{ color: '#64748b' }}>Email: </span>
                <span style={{ fontWeight: 600, color: '#1e293b' }}>{user?.email}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Editable Profile Form */}
        <form onSubmit={handleSave}>
          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label htmlFor="fullName" style={{ fontWeight: 600, color: '#334155' }}>
              Full Display Name
            </label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Your full name"
              required
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '0.9rem'
              }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '24px' }}>
            <label htmlFor="bio" style={{ fontWeight: 600, color: '#334155' }}>
              Professional Bio & Responsibilities
            </label>
            <textarea
              id="bio"
              rows={4}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Brief summary of your departmental responsibilities, focus areas, and internal notes..."
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '0.9rem',
                fontFamily: 'inherit'
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 20px' }}
            >
              <Save size={16} />
              <span>{loading ? 'Saving Profile...' : 'Save Profile Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
