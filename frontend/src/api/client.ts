// Centralized Typed API Client for Federated Agentic Mesh

const getApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // When running in the browser, routing through '/api/v1' enables Vite's built-in dev proxy
  // on port 5173. This eliminates Windows Firewall blocking port 8000 on LAN/Wi-Fi devices!
  return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

export interface User {
  id: number;
  email: string;
  full_name: string;
  department_id: number;
  role: 'admin' | 'department_manager' | 'department_employee';
  is_active: boolean;
  bio?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: number;
  title: string;
  department_scope: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageOut {
  id: number;
  conversation_id: string;
  sender_role: string;
  message?: string;
  content?: string;
  intent?: string;
  routed_departments?: string[];
  evidence_json?: any[];
  user_id?: number;
  agent_code?: string;
  evidence_metadata?: any;
  created_at?: string;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface DepartmentSummary {
  department_id: number;
  department_name: string;
  department_code: string;
  user_count: number;
  authorized_document_count: number;
  metrics: Record<string, number | string>;
}

export interface EvidenceReference {
  source_type: string;
  title: string;
  document_id?: number;
  chunk_id?: number;
  page_number?: number;
  department: string;
  snippet: string;
  confidence: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  routed_departments?: string[];
  requires_approval?: boolean;
  approval_id?: string;
  confidence?: number;
  evidence?: EvidenceReference[];
  error?: boolean;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  requested_department?: string;
  department_hint?: string;
}

export interface ChatResponse {
  answer: string;
  routed_departments: string[];
  requires_approval: boolean;
  approval_id?: string;
  correlation_id: string;
  confidence: number;
  evidence: EvidenceReference[];
}

export interface DocumentItem {
  id: number;
  title: string;
  filename: string;
  file_type: string;
  department_id: number;
  access_level: 'public' | 'internal' | 'confidential' | 'restricted';
  uploaded_by: number;
  status: 'processing' | 'indexed' | 'error' | 'empty';
  created_at: string;
}

export interface ApprovalRequestItem {
  id: string;
  requester_id: number;
  requester_department_id: number;
  action_type: string;
  target_resource: string;
  requested_operation: string;
  payload: Record<string, any>;
  status: 'pending' | 'approved' | 'rejected' | 'executed' | 'expired';
  idempotency_key: string;
  approver_id?: number;
  decision_reason?: string;
  created_at: string;
  expires_at?: string;
}

export interface AuditLogItem {
  id: number;
  actor_id?: number;
  actor_email?: string;
  actor_role: string;
  actor_department: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  outcome: string;
  reason?: string;
  correlation_id: string;
  timestamp: string;
}

export interface HealthReadyStatus {
  status: 'ready' | 'not_ready';
  dependencies: {
    database: { status: string };
    ollama_local_runtime: {
      status: string;
      model?: string;
      available?: boolean;
    };
  };
}

export interface DepartmentAgentItem {
  id: number;
  department_id: number;
  agent_code: string;
  name: string;
  description: string;
  system_prompt: string;
  is_enabled: boolean;
  error_count: number;
  last_error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FederationRequestItem {
  id: string;
  requester_user_id: number;
  requester_department_id: number;
  requesting_agent: string;
  source_department_id: number;
  business_purpose: string;
  requested_fields: string[];
  record_identifiers: string[];
  access_duration_minutes: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'REVOKED' | 'COMPLETED';
  approver_user_id?: number | null;
  decision_reason?: string | null;
  approved_fields?: string[] | null;
  approved_record_ids?: string[] | null;
  idempotency_key: string;
  created_at: string;
  decided_at?: string | null;
  expires_at: string;
  revoked_at?: string | null;
  used_at?: string | null;
  requester_email?: string;
  source_department_code?: string;
  requester_department_code?: string;
}

export interface FederationConsumeResult {
  request_id: string;
  status: string;
  source_department: string;
  released_fields: string[];
  record_count: number;
  records: Record<string, any>[];
}


class ApiClient {
  private getHeaders(isFormData = false): HeadersInit {
    const headers: Record<string, string> = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    const token = localStorage.getItem('mesh_access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const isFormData = options.body instanceof FormData;
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    
    let response: Response;
    try {
      response = await fetch(url, {
        ...options,
        headers: {
          ...this.getHeaders(isFormData),
          ...(options.headers || {})
        }
      });
    } catch (fetchErr: any) {
      // Dual-path fallback: If proxy path fails, automatically connect directly to port 8000
      if (!endpoint.startsWith('http') && typeof window !== 'undefined' && window.location.hostname) {
        const directUrl = `http://${window.location.hostname}:8000/api/v1${endpoint}`;
        try {
          response = await fetch(directUrl, {
            ...options,
            headers: {
              ...this.getHeaders(isFormData),
              ...(options.headers || {})
            }
          });
        } catch {
          throw new Error(`Failed to fetch from backend. Unable to connect to ${url} or ${directUrl}.`);
        }
      } else {
        throw fetchErr;
      }
    }

    if (response.status === 401) {
      localStorage.removeItem('mesh_access_token');
      localStorage.removeItem('mesh_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      throw new Error('Session expired. Please log in again.');
    }

    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}`;
      try {
        const errorJson = await response.json();
        errorMsg = errorJson.detail || errorJson.message || errorMsg;
      } catch {
        // use status text
      }
      throw new Error(errorMsg);
    }

    // Handles empty responses (e.g. 204 or void)
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<{ access_token: string; token_type: string; user: User }> {
    const data = await this.request<{ access_token: string; token_type: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    localStorage.setItem('mesh_access_token', data.access_token);
    localStorage.setItem('mesh_user', JSON.stringify(data.user));
    return data;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  logout() {
    localStorage.removeItem('mesh_access_token');
    localStorage.removeItem('mesh_user');
    window.location.href = '/login';
  }

  // Health
  async getHealthReady(): Promise<HealthReadyStatus> {
    // Root level health endpoint
    const rootUrl = API_BASE_URL.replace('/api/v1', '');
    const res = await fetch(`${rootUrl}/health/ready`);
    return res.json();
  }

  // Departments
  async getDepartments(): Promise<Department[]> {
    return this.request<Department[]>('/departments');
  }

  async getMyDepartmentSummary(): Promise<DepartmentSummary> {
    return this.request<DepartmentSummary>('/departments/me/summary');
  }

  async getDepartmentRecords(departmentCode: string): Promise<any[]> {
    return this.request<any[]>(`/departments/${departmentCode}/records`);
  }

  // Chat
  async sendChat(req: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(req)
    });
  }

  // Documents
  async getDocuments(): Promise<DocumentItem[]> {
    return this.request<DocumentItem[]>('/documents');
  }

  async uploadDocument(file: File, title: string, accessLevel: string): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('access_level', accessLevel);

    return this.request<DocumentItem>('/documents/upload', {
      method: 'POST',
      body: formData
    });
  }

  async deleteDocument(documentId: number): Promise<{ status: string; document_id: number }> {
    return this.request<{ status: string; document_id: number }>(`/documents/${documentId}`, {
      method: 'DELETE'
    });
  }

  // Approvals
  async getApprovals(statusFilter?: string): Promise<ApprovalRequestItem[]> {
    const q = statusFilter ? `?status_filter=${statusFilter}` : '';
    return this.request<ApprovalRequestItem[]>(`/approvals${q}`);
  }

  async approveRequest(approvalId: string, reason?: string): Promise<ApprovalRequestItem> {
    return this.request<ApprovalRequestItem>(`/approvals/${approvalId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ reason: reason || 'Approved via Web Dashboard' })
    });
  }

  async rejectRequest(approvalId: string, reason?: string): Promise<ApprovalRequestItem> {
    return this.request<ApprovalRequestItem>(`/approvals/${approvalId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason: reason || 'Rejected via Web Dashboard' })
    });
  }

  async executeApprovedAction(approvalId: string): Promise<any> {
    return this.request<any>(`/approvals/${approvalId}/execute`, {
      method: 'POST'
    });
  }

  // Audit Logs
  async getAuditLogs(params?: { department?: string; action?: string; outcome?: string; limit?: number; offset?: number }): Promise<AuditLogItem[]> {
    const sp = new URLSearchParams();
    if (params?.department) sp.append('department', params.department);
    if (params?.action) sp.append('action', params.action);
    if (params?.outcome) sp.append('outcome', params.outcome);
    if (params?.limit) sp.append('limit', params.limit.toString());
    if (params?.offset) sp.append('offset', params.offset.toString());
    const qs = sp.toString() ? `?${sp.toString()}` : '';
    return this.request<AuditLogItem[]>(`/audit${qs}`);
  }

  // Users Admin
  async getUsers(): Promise<User[]> {
    return this.request<User[]>('/users');
  }

  async createUser(data: { email: string; password: string; full_name: string; department_id: number; role: string; is_active: boolean }): Promise<User> {
    return this.request<User>('/users', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // Permissions
  async getMyPermissions(): Promise<any> {
    return this.request<any>('/permissions/me');
  }

  // Department Agents Admin
  async getAgents(): Promise<DepartmentAgentItem[]> {
    return this.request<DepartmentAgentItem[]>('/agents');
  }

  async toggleAgent(agentCode: string, isEnabled: boolean): Promise<DepartmentAgentItem> {
    return this.request<DepartmentAgentItem>(`/agents/${agentCode}/toggle?is_enabled=${isEnabled}`, {
      method: 'POST'
    });
  }

  async updateAgent(agentCode: string, data: Partial<DepartmentAgentItem>): Promise<DepartmentAgentItem> {
    return this.request<DepartmentAgentItem>(`/agents/${agentCode}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }

  // Federation Access Requests
  async getFederationRequests(status?: string): Promise<FederationRequestItem[]> {
    const q = status ? `?status=${status}` : '';
    return this.request<FederationRequestItem[]>(`/federation/requests${q}`);
  }

  async createFederationRequest(data: {
    source_department_code: string;
    business_purpose: string;
    requested_fields: string[];
    record_identifiers?: string[];
    access_duration_minutes?: number;
  }): Promise<FederationRequestItem> {
    return this.request<FederationRequestItem>('/federation/requests', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async decideFederationRequest(
    requestId: string,
    decision: 'approve' | 'reject',
    reason?: string,
    approvedFields?: string[],
    approvedRecordIds?: string[]
  ): Promise<FederationRequestItem> {
    return this.request<FederationRequestItem>(`/federation/requests/${requestId}/decision`, {
      method: 'POST',
      body: JSON.stringify({
        decision,
        reason,
        approved_fields: approvedFields,
        approved_record_ids: approvedRecordIds
      })
    });
  }

  async revokeFederationRequest(requestId: string, reason?: string): Promise<FederationRequestItem> {
    const q = reason ? `?reason=${encodeURIComponent(reason)}` : '';
    return this.request<FederationRequestItem>(`/federation/requests/${requestId}/revoke${q}`, {
      method: 'POST'
    });
  }

  async consumeFederationGrant(requestId: string): Promise<FederationConsumeResult> {
    return this.request<FederationConsumeResult>(`/federation/requests/${requestId}/consume`, {
      method: 'POST'
    });
  }

  // Persistent Conversations & History
  async getConversations(): Promise<Conversation[]> {
    return this.request<Conversation[]>('/chat/conversations');
  }

  async createConversation(data?: { title?: string; department_scope?: string }): Promise<Conversation> {
    return this.request<Conversation>('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify(data || {})
    });
  }

  async getConversationMessages(conversationId: string): Promise<ChatMessageOut[]> {
    return this.request<ChatMessageOut[]>(`/chat/conversations/${conversationId}/messages`);
  }

  async deleteConversation(conversationId: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/chat/conversations/${conversationId}`, {
      method: 'DELETE'
    });
  }

  // User Profile
  async updateProfile(data: { full_name?: string; bio?: string }): Promise<User> {
    const updated = await this.request<User>('/users/me', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    localStorage.setItem('mesh_user', JSON.stringify(updated));
    return updated;
  }

  async updateUser(userId: number, data: { full_name?: string; role?: string; department_id?: number; is_active?: boolean }): Promise<User> {
    return this.request<User>(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async deactivateUser(userId: number): Promise<{ status: string; id: number }> {
    return this.request<{ status: string; id: number }>(`/users/${userId}`, {
      method: 'DELETE'
    });
  }
}


export const api = new ApiClient();
