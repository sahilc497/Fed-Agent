import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, type User, type Department } from '../api/client';
import { 
  UserPlus, 
  X,
  AlertCircle
} from 'lucide-react';

export const UserAdmin: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // New user modal state
  const [showModal, setShowModal] = useState<boolean>(false);
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newDeptId, setNewDeptId] = useState<number>(1);
  const [newRole, setNewRole] = useState<string>('department_employee');
  const [createLoading, setCreateLoading] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [uList, dList] = await Promise.all([
        api.getUsers(),
        api.getDepartments()
      ]);
      setUsers(uList);
      setDepartments(dList);
    } catch (err: any) {
      setError(err.message || 'Failed to load enterprise user list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError(null);

    try {
      await api.createUser({
        email: newEmail,
        password: newPassword,
        full_name: newFullName,
        department_id: newDeptId,
        role: newRole,
        is_active: true
      });
      setShowModal(false);
      setNewEmail('');
      setNewPassword('');
      setNewFullName('');
      loadData();
    } catch (err: any) {
      setCreateError(err.message || 'Failed to provision user.');
    } finally {
      setCreateLoading(false);
    }
  };

  const getDeptName = (deptId: number) => {
    const d = departments.find((dept) => dept.id === deptId);
    return d ? d.name : `Dept #${deptId}`;
  };

  const formatRole = (role: string) => {
    switch (role) {
      case 'admin': return 'Administrator';
      case 'auditor': return 'Security Auditor';
      case 'department_manager': return 'Department Manager';
      case 'department_employee': return 'Staff Employee';
      default: return role;
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1>Enterprise User & Permissions Administration</h1>
          <p className="subtitle">
            Role-Based Access Control • Department Membership • Zero-Trust Policy Matrix
          </p>
        </div>

        {currentUser?.role === 'admin' && (
          <button 
            onClick={() => setShowModal(true)} 
            className="btn btn-primary"
            style={{ gap: '8px' }}
          >
            <UserPlus size={16} />
            <span>Provision User</span>
          </button>
        )}
      </div>

      {error ? (
        <div style={{ padding: '24px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', textAlign: 'center' }}>
          <AlertCircle size={32} style={{ margin: '0 auto 8px auto' }} />
          <div style={{ fontWeight: 600, fontSize: '1rem' }}>Administrative Access Restricted</div>
          <div style={{ fontSize: '0.9rem', marginTop: '4px' }}>{error}</div>
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          Loading user registry...
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Employee / User</th>
                <th>Email Address</th>
                <th>Assigned Department</th>
                <th>Assigned Role</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>#{u.id}</td>
                  <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                  <td>
                    <code>{u.email}</code>
                  </td>
                  <td>
                    <span className="badge badge-neutral">{getDeptName(u.department_id)}</span>
                  </td>
                  <td>
                    <span className={`badge ${u.role === 'admin' ? 'badge-danger' : (u.role === 'department_manager' ? 'badge-primary' : 'badge-neutral')}`}>
                      {formatRole(u.role)}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                      {u.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td>{new Date(u.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Provision User Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ fontWeight: 700, fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <UserPlus size={20} color="#2563eb" />
                <span>Provision New Enterprise User</span>
              </div>
              <button 
                onClick={() => setShowModal(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateUser}>
              <div className="modal-body">
                {createError && (
                  <div style={{ padding: '10px 14px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', borderRadius: '6px', fontSize: '0.85rem', marginBottom: '16px' }}>
                    {createError}
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="fullName">Full Name</label>
                  <input
                    id="fullName"
                    type="text"
                    value={newFullName}
                    onChange={(e) => setNewFullName(e.target.value)}
                    placeholder="e.g. Maya Lin"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="userEmail">Corporate Email</label>
                  <input
                    id="userEmail"
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="e.g. maya.lin@mesh.enterprise.internal"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="userPassword">Initial Password</label>
                  <input
                    id="userPassword"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="userDept">Department Assignment</label>
                  <select
                    id="userDept"
                    value={newDeptId}
                    onChange={(e) => setNewDeptId(Number(e.target.value))}
                  >
                    {departments.map((dept) => (
                      <option key={dept.id} value={dept.id}>
                        {dept.name} ({dept.code.toUpperCase()})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="userRole">Assigned Access Role</label>
                  <select
                    id="userRole"
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value)}
                  >
                    <option value="department_employee">Staff Employee (Department Scoped)</option>
                    <option value="department_manager">Department Manager (Approvals & Direct Access)</option>
                    <option value="auditor">Security Auditor (Read-Only Cross-Dept Audit)</option>
                    <option value="admin">Administrator (Full Enterprise Mesh Access)</option>
                  </select>
                </div>
              </div>

              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowModal(false)}
                  disabled={createLoading}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={createLoading}
                >
                  {createLoading ? 'Provisioning...' : 'Provision User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
