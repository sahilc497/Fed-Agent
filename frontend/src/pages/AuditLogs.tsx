import React, { useEffect, useState } from 'react';
import { api, type AuditLogItem } from '../api/client';
import { 
  ShieldAlert, 
  FileCheck
} from 'lucide-react';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [outcomeFilter, setOutcomeFilter] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  const loadAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const outcome = outcomeFilter === 'all' ? undefined : outcomeFilter;
      const data = await api.getAuditLogs({ outcome, limit: 100 });
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Audit logs could not be retrieved.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [outcomeFilter]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1>Immutable Security & Gateway Audit Trail</h1>
          <p className="subtitle">
            Tamper-evident log of all agent routing, cross-department bridges, and policy evaluations
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 600 }}>Outcome Filter:</span>
          <div style={{ display: 'flex', gap: '6px' }}>
            {['all', 'ALLOW', 'DENY'].map((o) => (
              <button
                key={o}
                type="button"
                className={`btn btn-sm ${outcomeFilter === o ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setOutcomeFilter(o)}
              >
                {o === 'all' ? 'All Outcomes' : o}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error ? (
        <div style={{ padding: '24px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', textAlign: 'center' }}>
          <ShieldAlert size={32} style={{ margin: '0 auto 8px auto' }} />
          <div style={{ fontWeight: 600, fontSize: '1rem' }}>Audit Access Restricted</div>
          <div style={{ fontSize: '0.9rem', marginTop: '4px' }}>{error}</div>
        </div>
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          Loading cryptographic audit records...
        </div>
      ) : logs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
          <FileCheck size={40} color="#94a3b8" style={{ margin: '0 auto 12px auto' }} />
          <div style={{ fontWeight: 600, fontSize: '1rem', color: '#1e293b' }}>No audit events found</div>
          <div style={{ fontSize: '0.85rem', marginTop: '4px' }}>
            No security events match the current filter parameters.
          </div>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Outcome</th>
                <th>Actor / User</th>
                <th>Action</th>
                <th>Resource Target</th>
                <th>Reason / Policy</th>
                <th>Correlation Request ID</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const isAllow = log.outcome.toLowerCase() === 'allow';
                return (
                  <tr key={log.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem', color: '#64748b' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td>
                      {isAllow ? (
                        <span className="badge badge-success">ALLOW</span>
                      ) : (
                        <span className="badge badge-danger">DENY</span>
                      )}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{log.actor_email || `Actor #${log.actor_id}`}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{log.actor_role} ({log.actor_department.toUpperCase()})</div>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600, color: '#1e293b' }}>{log.action}</span>
                    </td>
                    <td>
                      <span style={{ color: '#475569' }}>
                        {log.resource_type}{log.resource_id ? `: ${log.resource_id}` : ''}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: isAllow ? '#475569' : '#dc2626' }}>
                        {log.reason || 'Policy rule satisfied'}
                      </span>
                    </td>
                    <td>
                      <code style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {log.correlation_id}
                      </code>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
