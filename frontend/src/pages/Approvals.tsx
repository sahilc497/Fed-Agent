import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  api, 
  type ApprovalRequestItem, 
  type FederationRequestItem,
  type FederationConsumeResult
} from '../api/client';
import { 
  CheckSquare, 
  Check, 
  X, 
  Play, 
  Clock, 
  ShieldAlert,
  User,
  Share2,
  Plus,
  RefreshCw,
  Ban,
  CheckCircle2
} from 'lucide-react';

export const Approvals: React.FC = () => {
  const { user } = useAuth();
  
  // Tab state: 'federation' or 'operations'
  const [activeTab, setActiveTab] = useState<'federation' | 'operations'>('federation');

  // Sensitive Operations state
  const [approvals, setApprovals] = useState<ApprovalRequestItem[]>([]);
  const [opsFilter, setOpsFilter] = useState<string>('all');
  const [opsLoading, setOpsLoading] = useState<boolean>(true);
  const [selectedForDecision, setSelectedForDecision] = useState<{ id: string; type: 'approve' | 'reject' } | null>(null);
  const [decisionReason, setDecisionReason] = useState<string>('');

  // Federation Access Requests state
  const [fedRequests, setFedRequests] = useState<FederationRequestItem[]>([]);
  const [fedFilter, setFedFilter] = useState<string>('all');
  const [fedLoading, setFedLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Federation Decision Modal
  const [selectedFedDecision, setSelectedFedDecision] = useState<{
    request: FederationRequestItem;
    type: 'approve' | 'reject';
  } | null>(null);
  const [fedDecisionReason, setFedDecisionReason] = useState<string>('');
  const [approvedFieldsText, setApprovedFieldsText] = useState<string>('');

  // New Federation Request Modal
  const DEPT_FIELD_SUGGESTIONS: Record<string, string> = {
    sales: 'title, client_name, deal_value, stage',
    hr: 'full_name, position, leave_balance',
    finance: 'invoice_number, client_name, status',
    operations: 'sku, item_name, quantity_on_hand, status'
  };

  const [showNewModal, setShowNewModal] = useState<boolean>(false);
  const [newSourceDept, setNewSourceDept] = useState<string>('finance');
  const [newPurpose, setNewPurpose] = useState<string>('');
  const [newFields, setNewFields] = useState<string>('invoice_number, client_name, status');
  const [newRecordIds, setNewRecordIds] = useState<string>('');
  const [newDuration, setNewDuration] = useState<number>(60);
  const [newReqLoading, setNewReqLoading] = useState<boolean>(false);

  // Consume / Data Preview Modal
  const [consumeResult, setConsumeResult] = useState<FederationConsumeResult | null>(null);

  // Load Sensitive Operations
  const loadApprovals = async () => {
    setOpsLoading(true);
    try {
      const statusParam = opsFilter === 'all' ? undefined : opsFilter;
      const data = await api.getApprovals(statusParam);
      setApprovals(data);
    } finally {
      setOpsLoading(false);
    }
  };

  // Load Federation Requests
  const loadFedRequests = async () => {
    setFedLoading(true);
    try {
      const statusParam = fedFilter === 'all' ? undefined : fedFilter;
      const data = await api.getFederationRequests(statusParam);
      setFedRequests(data);
    } finally {
      setFedLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'operations') {
      loadApprovals();
    } else {
      loadFedRequests();
    }
  }, [activeTab, opsFilter, fedFilter]);

  // Handle Operations Decision
  const handleDecision = async () => {
    if (!selectedForDecision) return;
    const { id, type } = selectedForDecision;
    setActionLoading(id);

    try {
      if (type === 'approve') {
        await api.approveRequest(id, decisionReason || 'Approved via Web Dashboard');
      } else {
        await api.rejectRequest(id, decisionReason || 'Rejected via Web Dashboard');
      }
      setSelectedForDecision(null);
      setDecisionReason('');
      loadApprovals();
    } catch (err: any) {
      alert(`Decision failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Operations Execute
  const handleExecute = async (id: string) => {
    if (!window.confirm('Execute this approved action with idempotency verification?')) return;
    setActionLoading(id);
    try {
      await api.executeApprovedAction(id);
      loadApprovals();
    } catch (err: any) {
      alert(`Execution failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Federation Decision (Approve / Reject)
  const handleFedDecision = async () => {
    if (!selectedFedDecision) return;
    const { request, type } = selectedFedDecision;
    setActionLoading(request.id);

    try {
      const fieldsList = approvedFieldsText
        ? approvedFieldsText.split(',').map(s => s.trim()).filter(Boolean)
        : request.requested_fields;

      await api.decideFederationRequest(
        request.id,
        type,
        fedDecisionReason || (type === 'approve' ? 'Approved by security policy' : 'Request rejected by admin'),
        type === 'approve' ? fieldsList : undefined
      );

      setSelectedFedDecision(null);
      setFedDecisionReason('');
      setApprovedFieldsText('');
      loadFedRequests();
    } catch (err: any) {
      alert(`Decision failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Federation Revoke
  const handleRevokeGrant = async (requestId: string) => {
    const reason = prompt('Enter revocation reason (mandatory for audit log):', 'Revoked by security administrator');
    if (reason === null) return;
    setActionLoading(requestId);
    try {
      await api.revokeFederationRequest(requestId, reason || 'Manual revocation');
      loadFedRequests();
    } catch (err: any) {
      alert(`Revocation failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Federation Consume (Test grant & retrieve filtered records)
  const handleConsumeGrant = async (requestId: string) => {
    setActionLoading(requestId);
    try {
      const result = await api.consumeFederationGrant(requestId);
      setConsumeResult(result);
    } catch (err: any) {
      alert(`Access failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Create New Federation Request
  const handleCreateNewRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPurpose.trim()) {
      alert('Business purpose is required.');
      return;
    }
    setNewReqLoading(true);
    try {
      const fieldsList = newFields.split(',').map(s => s.trim()).filter(Boolean);
      const recordIdsList = newRecordIds ? newRecordIds.split(',').map(s => s.trim()).filter(Boolean) : undefined;

      await api.createFederationRequest({
        source_department_code: newSourceDept,
        business_purpose: newPurpose.trim(),
        requested_fields: fieldsList,
        record_identifiers: recordIdsList,
        access_duration_minutes: Number(newDuration) || 60
      });

      setShowNewModal(false);
      setNewPurpose('');
      setNewRecordIds('');
      loadFedRequests();
    } catch (err: any) {
      alert(`Failed to create request: ${err.message}`);
    } finally {
      setNewReqLoading(false);
    }
  };

  const isAdmin = user?.role === 'admin';
  const canApproveOps = user?.role === 'admin' || user?.role === 'department_manager';

  const getFedBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'PENDING': return <span className="badge badge-warning">Pending Admin Review</span>;
      case 'APPROVED': return <span className="badge badge-success">Approved Grant</span>;
      case 'REJECTED': return <span className="badge badge-danger">Rejected</span>;
      case 'REVOKED': return <span className="badge badge-danger">Revoked</span>;
      case 'EXPIRED': return <span className="badge badge-neutral">Expired</span>;
      case 'COMPLETED': return <span className="badge badge-primary">Completed / Consumed</span>;
      default: return <span className="badge badge-neutral">{status}</span>;
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h1>Governance, Approvals & Federation</h1>
          <p className="subtitle">
            Admin-Controlled Data Federation • Anti-Self-Approval • Department Boundary Enforced
          </p>
        </div>

        {activeTab === 'federation' && (
          <button 
            type="button" 
            className="btn btn-primary"
            style={{ gap: '8px' }}
            onClick={() => setShowNewModal(true)}
          >
            <Plus size={16} />
            <span>Request Cross-Dept Access</span>
          </button>
        )}
      </div>

      {/* Primary Tab Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '2px solid #e2e8f0', marginBottom: '24px' }}>
        <button
          type="button"
          onClick={() => setActiveTab('federation')}
          style={{
            padding: '10px 18px',
            fontSize: '0.95rem',
            fontWeight: 600,
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'federation' ? '3px solid #2563eb' : '3px solid transparent',
            color: activeTab === 'federation' ? '#2563eb' : '#64748b',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <Share2 size={18} />
          <span>Federation Access Requests</span>
          <span className="badge badge-neutral" style={{ fontSize: '0.75rem' }}>
            {fedRequests.filter(r => r.status === 'PENDING').length} Pending
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('operations')}
          style={{
            padding: '10px 18px',
            fontSize: '0.95rem',
            fontWeight: 600,
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'operations' ? '3px solid #2563eb' : '3px solid transparent',
            color: activeTab === 'operations' ? '#2563eb' : '#64748b',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <CheckSquare size={18} />
          <span>Sensitive Operations</span>
          <span className="badge badge-neutral" style={{ fontSize: '0.75rem' }}>
            {approvals.filter(a => a.status === 'pending').length} Pending
          </span>
        </button>
      </div>

      {/* TAB 1: FEDERATION ACCESS REQUESTS */}
      {activeTab === 'federation' && (
        <div>
          {/* Controls Bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', gap: '6px' }}>
              {['all', 'PENDING', 'APPROVED', 'REJECTED', 'REVOKED', 'EXPIRED'].map((st) => (
                <button
                  key={st}
                  type="button"
                  className={`btn btn-sm ${fedFilter === st ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setFedFilter(st)}
                >
                  {st.charAt(0).toUpperCase() + st.slice(1).toLowerCase()}
                </button>
              ))}
            </div>

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={loadFedRequests}
              style={{ gap: '6px' }}
            >
              <RefreshCw size={14} />
              <span>Refresh</span>
            </button>
          </div>

          {fedLoading ? (
            <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
              Loading federation access requests...
            </div>
          ) : fedRequests.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
              <Share2 size={40} color="#94a3b8" style={{ margin: '0 auto 12px auto' }} />
              <div style={{ fontWeight: 600, fontSize: '1rem', color: '#1e293b' }}>No federation access requests found</div>
              <div style={{ fontSize: '0.85rem', marginTop: '4px' }}>
                Cross-department access requests submitted by department agents will appear here for administrative approval.
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {fedRequests.map((req) => {
                const isSelfRequest = user?.id === req.requester_user_id;
                const isPending = req.status === 'PENDING';
                const isApproved = req.status === 'APPROVED';

                return (
                  <div 
                    key={req.id} 
                    className="card" 
                    style={{ 
                      borderLeft: isPending ? '4px solid #f59e0b' : (isApproved ? '4px solid #10b981' : undefined) 
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
                            Cross-Department Request: <span style={{ textTransform: 'uppercase', color: '#2563eb' }}>{req.source_department_code || `Dept #${req.source_department_id}`}</span> Data
                          </span>
                          {getFedBadge(req.status)}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                          Request ID: <code>{req.id}</code> • Requesting Agent: <code>{req.requesting_agent}</code>
                        </div>
                      </div>

                      <div style={{ fontSize: '0.75rem', color: '#64748b', textAlign: 'right' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                          <Clock size={13} />
                          <span>Submitted: {new Date(req.created_at).toLocaleString()}</span>
                        </div>
                        {req.expires_at && (
                          <div style={{ color: isApproved ? '#059669' : '#64748b', marginTop: '2px' }}>
                            Expires: {new Date(req.expires_at).toLocaleTimeString()}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Metadata Grid */}
                    <div className="grid-2" style={{ marginBottom: '14px', background: '#f8fafc', padding: '12px 16px', borderRadius: '8px' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>REQUESTING IDENTITY & PURPOSE</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b', marginTop: '2px' }}>
                          {req.requester_email || `User #${req.requester_user_id}`} ({req.requester_department_code?.toUpperCase() || 'Requester Dept'})
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#475569', marginTop: '4px' }}>
                          <strong>Purpose:</strong> {req.business_purpose}
                        </div>
                      </div>

                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>REQUESTED FIELDS</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                          {req.requested_fields.map((f, i) => (
                            <span key={i} className="badge badge-neutral" style={{ fontSize: '0.75rem' }}>
                              {f}
                            </span>
                          ))}
                        </div>
                        {req.record_identifiers && req.record_identifiers.length > 0 && (
                          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '6px' }}>
                            Target IDs: <code>{req.record_identifiers.join(', ')}</code>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Decision info */}
                    {req.decision_reason && (
                      <div style={{ fontSize: '0.85rem', color: '#475569', fontStyle: 'italic', marginBottom: '14px', background: '#f1f5f9', padding: '8px 12px', borderRadius: '6px' }}>
                        Admin Decision Note: "{req.decision_reason}"
                        {req.approved_fields && (
                          <div style={{ marginTop: '4px', fontStyle: 'normal', fontSize: '0.8rem', color: '#059669' }}>
                            Approved Fields Released: <strong>{req.approved_fields.join(', ')}</strong>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Actions Footer */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #e2e8f0', paddingTop: '14px' }}>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <User size={14} />
                        <span>Submitted by {req.requester_email || `User #${req.requester_user_id}`}</span>
                        {isSelfRequest && <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>You submitted this</span>}
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        {isPending && (
                          <>
                            {isSelfRequest && !isAdmin ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#d97706', background: '#fffbeb', padding: '6px 12px', borderRadius: '6px' }}>
                                <ShieldAlert size={14} />
                                <span>Anti-Self-Approval Enforced</span>
                              </div>
                            ) : isAdmin ? (
                              <>
                                <button
                                  type="button"
                                  className="btn btn-secondary btn-sm"
                                  onClick={() => {
                                    setSelectedFedDecision({ request: req, type: 'reject' });
                                    setFedDecisionReason('');
                                  }}
                                  disabled={actionLoading === req.id}
                                  style={{ color: '#ef4444', borderColor: '#fecaca' }}
                                >
                                  <X size={14} />
                                  <span>Reject</span>
                                </button>

                                <button
                                  type="button"
                                  className="btn btn-primary btn-sm"
                                  onClick={() => {
                                    setSelectedFedDecision({ request: req, type: 'approve' });
                                    setApprovedFieldsText(req.requested_fields.join(', '));
                                    setFedDecisionReason('Approved for authorized task');
                                  }}
                                  disabled={actionLoading === req.id}
                                  style={{ backgroundColor: '#10b981' }}
                                >
                                  <Check size={14} />
                                  <span>Approve Grant</span>
                                </button>
                              </>
                            ) : (
                              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Awaiting administrator review</span>
                            )}
                          </>
                        )}

                        {isApproved && (
                          <>
                            <button
                              type="button"
                              className="btn btn-primary btn-sm"
                              onClick={() => handleConsumeGrant(req.id)}
                              disabled={actionLoading === req.id}
                              style={{ backgroundColor: '#2563eb', gap: '6px' }}
                            >
                              <Play size={14} />
                              <span>Test & Retrieve Data</span>
                            </button>

                            {isAdmin && (
                              <button
                                type="button"
                                className="btn btn-secondary btn-sm"
                                onClick={() => handleRevokeGrant(req.id)}
                                disabled={actionLoading === req.id}
                                style={{ color: '#dc2626', borderColor: '#fecaca', gap: '6px' }}
                              >
                                <Ban size={14} />
                                <span>Revoke Grant</span>
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: SENSITIVE OPERATIONS */}
      {activeTab === 'operations' && (
        <div>
          {/* Filter Pills */}
          <div style={{ display: 'flex', gap: '6px', marginBottom: '20px' }}>
            {['all', 'pending', 'approved', 'rejected', 'executed'].map((st) => (
              <button
                key={st}
                type="button"
                className={`btn btn-sm ${opsFilter === st ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setOpsFilter(st)}
              >
                {st.charAt(0).toUpperCase() + st.slice(1)}
              </button>
            ))}
          </div>

          {opsLoading ? (
            <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
              Loading approval requests...
            </div>
          ) : approvals.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
              <CheckSquare size={40} color="#94a3b8" style={{ margin: '0 auto 12px auto' }} />
              <div style={{ fontWeight: 600, fontSize: '1rem', color: '#1e293b' }}>No sensitive operations found</div>
              <div style={{ fontSize: '0.85rem', marginTop: '4px' }}>
                No actions match the selected status filter for your department scope.
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {approvals.map((appr) => {
                const isSelfRequest = user?.id === appr.requester_id;
                const isPending = appr.status === 'pending';
                const isApproved = appr.status === 'approved';

                return (
                  <div key={appr.id} className="card" style={{ borderLeft: appr.status === 'pending' ? '4px solid #f59e0b' : (appr.status === 'approved' ? '4px solid #10b981' : undefined) }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
                            {appr.action_type.replace(/_/g, ' ').toUpperCase()}
                          </span>
                          <span className="badge badge-warning">{appr.status}</span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                          Request ID: <code>{appr.id}</code> • Idempotency: <code>{appr.idempotency_key}</code>
                        </div>
                      </div>

                      <div style={{ fontSize: '0.75rem', color: '#64748b', textAlign: 'right' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                          <Clock size={13} />
                          <span>{new Date(appr.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid-2" style={{ marginBottom: '14px', background: '#f8fafc', padding: '12px 16px', borderRadius: '8px' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>TARGET RESOURCE</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b', marginTop: '2px' }}>
                          {appr.target_resource}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>OPERATION</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b', marginTop: '2px' }}>
                          {appr.requested_operation}
                        </div>
                      </div>
                    </div>

                    {/* Payload display */}
                    {appr.payload && (
                      <div style={{ marginBottom: '14px' }}>
                        <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, marginBottom: '4px' }}>OPERATION PAYLOAD</div>
                        <pre style={{
                          backgroundColor: '#0f172a',
                          color: '#f8fafc',
                          padding: '10px 14px',
                          borderRadius: '6px',
                          fontSize: '0.8rem',
                          overflowX: 'auto',
                          fontFamily: 'monospace'
                        }}>
                          {JSON.stringify(appr.payload, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Decision reason */}
                    {appr.decision_reason && (
                      <div style={{ fontSize: '0.85rem', color: '#475569', fontStyle: 'italic', marginBottom: '14px', background: '#f1f5f9', padding: '8px 12px', borderRadius: '6px' }}>
                        Decision Note: "{appr.decision_reason}"
                      </div>
                    )}

                    {/* Actions Footer */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #e2e8f0', paddingTop: '14px' }}>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <User size={14} />
                        <span>Requester User #{appr.requester_id}</span>
                        {isSelfRequest && <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>You requested this</span>}
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        {isPending && (
                          <>
                            {isSelfRequest ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#d97706', background: '#fffbeb', padding: '6px 12px', borderRadius: '6px' }}>
                                <ShieldAlert size={14} />
                                <span>Self-Approval Prohibited by Policy</span>
                              </div>
                            ) : canApproveOps ? (
                              <>
                                <button
                                  type="button"
                                  className="btn btn-secondary btn-sm"
                                  onClick={() => setSelectedForDecision({ id: appr.id, type: 'reject' })}
                                  disabled={actionLoading === appr.id}
                                  style={{ color: '#ef4444', borderColor: '#fecaca' }}
                                >
                                  <X size={14} />
                                  <span>Reject</span>
                                </button>
                                <button
                                  type="button"
                                  className="btn btn-primary btn-sm"
                                  onClick={() => setSelectedForDecision({ id: appr.id, type: 'approve' })}
                                  disabled={actionLoading === appr.id}
                                  style={{ backgroundColor: '#10b981' }}
                                >
                                  <Check size={14} />
                                  <span>Approve</span>
                                </button>
                              </>
                            ) : (
                              <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Awaiting manager review</span>
                            )}
                          </>
                        )}

                        {isApproved && (
                          <button
                            type="button"
                            className="btn btn-primary btn-sm"
                            onClick={() => handleExecute(appr.id)}
                            disabled={actionLoading === appr.id}
                            style={{ backgroundColor: '#2563eb', gap: '6px' }}
                          >
                            <Play size={14} />
                            <span>Execute Action</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* MODAL 1: Federation Decision (Approve / Reject) */}
      {selectedFedDecision && (
        <div className="modal-overlay" onClick={() => setSelectedFedDecision(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                {selectedFedDecision.type === 'approve' 
                  ? 'Approve Cross-Department Data Grant' 
                  : 'Reject Federation Access Request'}
              </div>
            </div>

            <div className="modal-body">
              <p style={{ fontSize: '0.875rem', color: '#475569', marginBottom: '14px' }}>
                {selectedFedDecision.type === 'approve'
                  ? 'Authorizing this request will grant the requesting agent temporary, audited access to explicitly approved fields only.'
                  : 'Rejecting this request will permanently prevent the requesting agent from retrieving these cross-department records.'}
              </p>

              {selectedFedDecision.type === 'approve' && (
                <div className="form-group" style={{ marginBottom: '14px' }}>
                  <label htmlFor="approvedFieldsInput">Explicit Approved Fields (Comma-separated)</label>
                  <input
                    id="approvedFieldsInput"
                    type="text"
                    value={approvedFieldsText}
                    onChange={(e) => setApprovedFieldsText(e.target.value)}
                    placeholder="e.g. order_id, payment_status, total_amount"
                  />
                  <small style={{ color: '#64748b', fontSize: '0.75rem' }}>
                    Only the exact fields listed here will be released by the Federation Gateway.
                  </small>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="fedReasonText">Administrator Reason / Audit Note</label>
                <textarea
                  id="fedReasonText"
                  rows={3}
                  value={fedDecisionReason}
                  onChange={(e) => setFedDecisionReason(e.target.value)}
                  placeholder="e.g. Approved order verification for sales fulfillment task."
                  required
                />
              </div>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={() => setSelectedFedDecision(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className={`btn ${selectedFedDecision.type === 'approve' ? 'btn-primary' : 'btn-danger'}`}
                onClick={handleFedDecision}
                disabled={actionLoading === selectedFedDecision.request.id}
                style={{ backgroundColor: selectedFedDecision.type === 'approve' ? '#10b981' : undefined }}
              >
                Confirm {selectedFedDecision.type === 'approve' ? 'Approval' : 'Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: Create New Federation Request */}
      {showNewModal && (
        <div className="modal-overlay" onClick={() => setShowNewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleCreateNewRequest}>
              <div className="modal-header">
                <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                  Request Cross-Department Data Access
                </div>
              </div>

              <div className="modal-body">
                <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '14px' }}>
                  Submit an audited request through the Federation Gateway. Cross-department queries remain blocked until an administrator approves.
                </p>

                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label htmlFor="sourceDept">Source Department</label>
                  <select 
                    id="sourceDept" 
                    value={newSourceDept} 
                    onChange={(e) => {
                      const dept = e.target.value;
                      setNewSourceDept(dept);
                      setNewFields(DEPT_FIELD_SUGGESTIONS[dept] || '');
                    }}
                  >
                    <option value="sales">Sales (Proposals, Deals, CRM)</option>
                    <option value="hr">HR (Employee Directory, PTO)</option>
                    <option value="finance">Finance (Invoices, Payment Status)</option>
                    <option value="operations">Operations (Warehouse Inventory, Logistics)</option>
                  </select>
                </div>

                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label htmlFor="purpose">Business Purpose / Justification</label>
                  <textarea
                    id="purpose"
                    rows={2}
                    value={newPurpose}
                    onChange={(e) => setNewPurpose(e.target.value)}
                    placeholder="e.g. Need to verify customer payment status before shipping warehouse order."
                    required
                  />
                </div>

                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label htmlFor="reqFields">Requested Fields (Comma-separated)</label>
                  <input
                    id="reqFields"
                    type="text"
                    value={newFields}
                    onChange={(e) => setNewFields(e.target.value)}
                    placeholder={`e.g. ${DEPT_FIELD_SUGGESTIONS[newSourceDept] || 'field1, field2'}`}
                    required
                  />
                  <small style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '4px', display: 'block' }}>
                    Valid {newSourceDept.toUpperCase()} fields: <code>{DEPT_FIELD_SUGGESTIONS[newSourceDept]}</code>
                  </small>
                </div>

                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label htmlFor="recIds">Specific Record Identifiers (Optional, comma-separated)</label>
                  <input
                    id="recIds"
                    type="text"
                    value={newRecordIds}
                    onChange={(e) => setNewRecordIds(e.target.value)}
                    placeholder="e.g. ORD-1001, ORD-1002"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="duration">Grant Duration (Minutes)</label>
                  <input
                    id="duration"
                    type="number"
                    min={5}
                    max={1440}
                    value={newDuration}
                    onChange={(e) => setNewDuration(Number(e.target.value))}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowNewModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={newReqLoading}
                >
                  {newReqLoading ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Consume Grant Preview */}
      {consumeResult && (
        <div className="modal-overlay" onClick={() => setConsumeResult(null)}>
          <div className="modal-content" style={{ maxWidth: '700px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '1.1rem' }}>
                <CheckCircle2 color="#10b981" size={20} />
                <span>Federation Gateway: Data Released</span>
              </div>
            </div>

            <div className="modal-body">
              <div style={{ background: '#f8fafc', padding: '12px 14px', borderRadius: '8px', marginBottom: '14px', fontSize: '0.85rem' }}>
                <div><strong>Source Department:</strong> {consumeResult.source_department.toUpperCase()}</div>
                <div><strong>Released Fields:</strong> {consumeResult.released_fields.join(', ')}</div>
                <div><strong>Records Returned:</strong> {consumeResult.record_count}</div>
              </div>

              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, marginBottom: '6px' }}>
                FILTERED RECORDS PAYLOAD (MINIMUM AUTHORIZED ATTRIBUTES ONLY):
              </div>
              <pre style={{
                backgroundColor: '#0f172a',
                color: '#f8fafc',
                padding: '12px 16px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                maxHeight: '300px',
                overflowY: 'auto',
                fontFamily: 'monospace'
              }}>
                {JSON.stringify(consumeResult.records, null, 2)}
              </pre>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={() => setConsumeResult(null)}
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: Operations Decision Modal */}
      {selectedForDecision && (
        <div className="modal-overlay" onClick={() => setSelectedForDecision(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                {selectedForDecision.type === 'approve' ? 'Authorize & Approve Action' : 'Reject Action Request'}
              </div>
            </div>

            <div className="modal-body">
              <p style={{ fontSize: '0.875rem', color: '#475569', marginBottom: '14px' }}>
                Please provide an audit justification note for this decision.
              </p>

              <div className="form-group">
                <label htmlFor="reasonText">Decision Justification / Reason</label>
                <textarea
                  id="reasonText"
                  rows={3}
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  placeholder="e.g. Verified dual-authorization; approved for processing."
                  required
                />
              </div>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={() => setSelectedForDecision(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className={`btn ${selectedForDecision.type === 'approve' ? 'btn-primary' : 'btn-danger'}`}
                onClick={handleDecision}
              >
                Confirm {selectedForDecision.type === 'approve' ? 'Approval' : 'Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

