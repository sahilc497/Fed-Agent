import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { 
  ShieldCheck, 
  AlertCircle,
  Lock
} from 'lucide-react';

export const DepartmentView: React.FC = () => {
  const { user } = useAuth();
  
  // Default to user's department, or sales if admin
  const [selectedDept, setSelectedDept] = useState<string>('sales');
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      if (user.role === 'admin' || user.role === 'auditor') {
        setSelectedDept('sales');
      } else {
        const userDeptCode = user.department_id === 1 ? 'sales' : (user.department_id === 2 ? 'hr' : (user.department_id === 3 ? 'finance' : 'operations'));
        setSelectedDept(userDeptCode);
      }
    }
  }, [user]);

  useEffect(() => {
    let isMounted = true;
    const fetchRecords = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getDepartmentRecords(selectedDept);
        if (isMounted) setRecords(data);
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || `Access to ${selectedDept.toUpperCase()} records denied by isolation policy.`);
          setRecords([]);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchRecords();
    return () => { isMounted = false; };
  }, [selectedDept]);

  const canSwitchDepts = user?.role === 'admin' || user?.role === 'auditor';

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1>Department Records & Business Data</h1>
          <p className="subtitle">
            Zero-Trust Departmental Data Isolation • Sensitive Field Filtering
          </p>
        </div>

        {canSwitchDepts ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>Switch Scope:</span>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button 
                type="button"
                className={`btn btn-sm ${selectedDept === 'sales' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedDept('sales')}
              >
                Sales Pipeline
              </button>
              <button 
                type="button"
                className={`btn btn-sm ${selectedDept === 'hr' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedDept('hr')}
              >
                HR Roster
              </button>
              <button 
                type="button"
                className={`btn btn-sm ${selectedDept === 'finance' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedDept('finance')}
              >
                Finance Invoices
              </button>
              <button 
                type="button"
                className={`btn btn-sm ${selectedDept === 'operations' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedDept('operations')}
              >
                Operations Inventory
              </button>
            </div>
          </div>
        ) : (
          <div className="badge badge-neutral">
            Scoped to: {selectedDept.toUpperCase()}
          </div>
        )}
      </div>

      {/* Security Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 18px',
        backgroundColor: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: '8px',
        color: '#1e40af',
        fontSize: '0.85rem',
        marginBottom: '24px'
      }}>
        <ShieldCheck size={20} color="#2563eb" style={{ flexShrink: 0 }} />
        <div>
          <strong>Federation Gateway Active: </strong>
          {selectedDept === 'hr' && (
            <span>Confidential employee salaries are masked for non-managerial staff. Only authorized personnel can see unredacted compensation.</span>
          )}
          {selectedDept === 'sales' && (
            <span>Pipeline records and client opportunities are isolated. Cross-department queries route through the Gateway.</span>
          )}
          {selectedDept === 'finance' && (
            <span>Receivables, overdue invoices, and wire disbursements are protected with strict audit logging.</span>
          )}
          {selectedDept === 'operations' && (
            <span>Warehouse stock, equipment SKUs, and supply chain records are scoped strictly to Operations personnel.</span>
          )}
        </div>
      </div>


      {error ? (
        <div style={{
          padding: '24px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          color: '#991b1b',
          textAlign: 'center'
        }}>
          <AlertCircle size={32} style={{ margin: '0 auto 8px auto' }} />
          <div style={{ fontWeight: 600, fontSize: '1rem' }}>Zero-Trust Access Denial</div>
          <div style={{ fontSize: '0.9rem', marginTop: '4px' }}>{error}</div>
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          Loading authorized departmental records...
        </div>
      ) : records.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          No records found for this department.
        </div>
      ) : (
        <div className="table-container">
          {/* Sales Table */}
          {selectedDept === 'sales' && (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Opportunity Title</th>
                  <th>Client Name</th>
                  <th>Deal Value</th>
                  <th>Stage</th>
                  <th>Finance Review</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>#{r.id}</td>
                    <td style={{ fontWeight: 600 }}>{r.title}</td>
                    <td>{r.client_name}</td>
                    <td style={{ fontWeight: 600, color: '#0f172a' }}>
                      ${r.deal_value.toLocaleString()}
                    </td>
                    <td>
                      <span className="badge badge-neutral">{r.stage}</span>
                    </td>
                    <td>
                      {r.needs_finance_approval ? (
                        <span className="badge badge-warning">Required</span>
                      ) : (
                        <span className="badge badge-neutral">Standard</span>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${r.finance_status === 'approved' ? 'badge-success' : (r.finance_status === 'pending' ? 'badge-warning' : 'badge-neutral')}`}>
                        {r.finance_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* HR Table */}
          {selectedDept === 'hr' && (
            <table>
              <thead>
                <tr>
                  <th>Employee Code</th>
                  <th>Full Name</th>
                  <th>Position</th>
                  <th>Leave Balance</th>
                  <th>Compensation (Salary)</th>
                  <th>Performance Rating</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td><code>{r.employee_code}</code></td>
                    <td style={{ fontWeight: 600 }}>{r.full_name}</td>
                    <td>{r.position}</td>
                    <td>{r.leave_balance} Days</td>
                    <td>
                      {r.salary !== null ? (
                        <span style={{ fontWeight: 600, color: '#047857' }}>
                          ${r.salary.toLocaleString()}
                        </span>
                      ) : (
                        <span style={{ color: '#94a3b8', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Lock size={12} />
                          <span>Restricted (Masked)</span>
                        </span>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${r.performance_rating === 'Exceeds Expectations' ? 'badge-success' : 'badge-neutral'}`}>
                        {r.performance_rating}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Finance Table */}
          {selectedDept === 'finance' && (
            <table>
              <thead>
                <tr>
                  <th>Invoice Number</th>
                  <th>Client Name</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Due Date</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td><code>{r.invoice_number}</code></td>
                    <td style={{ fontWeight: 600 }}>{r.client_name}</td>
                    <td style={{ fontWeight: 600, color: '#0f172a' }}>
                      ${r.amount.toLocaleString()}
                    </td>
                    <td>
                      <span className={`badge ${r.status === 'paid' ? 'badge-success' : (r.status === 'overdue' ? 'badge-danger' : 'badge-warning')}`}>
                        {r.status.toUpperCase()}
                      </span>
                    </td>
                    <td>{new Date(r.due_date).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Operations Table */}
          {selectedDept === 'operations' && (
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Item Name</th>
                  <th>Category</th>
                  <th>Quantity on Hand</th>
                  <th>Reorder Level</th>
                  <th>Warehouse Location</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td><code>{r.sku}</code></td>
                    <td style={{ fontWeight: 600 }}>{r.item_name}</td>
                    <td>{r.category}</td>
                    <td style={{ fontWeight: 600, color: '#0f172a' }}>
                      {r.quantity_on_hand.toLocaleString()} units
                    </td>
                    <td>{r.reorder_threshold.toLocaleString()} units</td>
                    <td>{r.warehouse_location}</td>
                    <td>
                      <span className={`badge ${r.status === 'in_stock' ? 'badge-success' : (r.status === 'low_stock' ? 'badge-warning' : 'badge-danger')}`}>
                        {r.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

      )}
    </div>
  );
};
