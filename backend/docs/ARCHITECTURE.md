# Federated Agentic Mesh — Architecture & Security Blueprint

## 1. Executive Summary

The **Federated Agentic Mesh** is a local-first enterprise AI backend enabling employees across different departments (Sales, HR, Finance) to interact via a unified conversational interface while strictly preserving department data privacy, enforcing zero-trust authorization boundaries, and requiring human approvals for sensitive actions.

All AI model inference is hosted locally on the machine via **Ollama**, ensuring confidential enterprise data never leaves the local perimeter.

---

## 2. System Architecture Diagram

```mermaid
graph TD
    Client[Employee / Client Application] -->|JWT Auth Token| FastAPI[FastAPI REST API /api/v1]
    
    FastAPI --> AuthPolicy[Authentication & Permission Engine]
    AuthPolicy --> Orchestrator[Department-Aware Orchestrator]
    
    Orchestrator --> Router[Intent Router (6 Canonical Intents)]
    
    Router -->|Intent: sales| SalesAgent[Sales Agent]
    Router -->|Intent: hr| HRAgent[HR Agent]
    Router -->|Intent: finance| FinanceAgent[Finance Agent]
    Router -->|Intent: multi_dept| MultiOrchestration[Multi-Agent Coordination]
    Router -->|Intent: operations| OperationsDeferred[Operations (Phase 2 Deferred)]
    
    SalesAgent --> SalesData[(Sales DB & Vectors)]
    HRAgent --> HRData[(HR DB & Vectors)]
    FinanceAgent --> FinanceData[(Finance DB & Vectors)]
    
    SalesAgent -.->|Cross-Dept Query| Gateway[Federation Gateway]
    MultiOrchestration -.-> Gateway
    Gateway -->|Strict Field Filtering & Policy Check| FinanceData
    
    FinanceAgent -->|Sensitive Action| ApprovalWorkflow[Human Approval Workflow]
    ApprovalWorkflow --> Approver[Manager / Admin Approval Decision]
    
    SalesAgent --> Audit[(Append-Only Audit Logs)]
    HRAgent --> Audit
    FinanceAgent --> Audit
    Gateway --> Audit
    ApprovalWorkflow --> Audit
    
    Orchestrator -->|Grounded Evidence Only| LocalOllama[Local Ollama (qwen3:8b)]
    LocalOllama --> Orchestrator
    Orchestrator --> Client
```

---

## 3. Core Architectural Components

### A. Central Orchestrator & Intent Classifier
- Classifies requests into 6 canonical labels: `sales`, `hr`, `finance`, `operations`, `multi_department`, `unknown`.
- `operations` is recognized as deferred to Phase 2 rather than failing to route.
- Replaces prompt-based routing with explicit, testable policy logic and a swappable ML classifier interface.

### B. Federation Gateway
- **The ultimate cross-department security boundary.**
- Direct agent-to-agent cross-department calls are forbidden.
- Validates the calling agent, requesting user, business purpose, and target department contract.
- Strips prohibited fields (e.g. `salary`, `bank_details`, `profit_margins`).
- Records immutable `allow` and `deny` audit log events for every attempt.

### C. Department Agents (`SalesAgent`, `HRAgent`, `FinanceAgent`)
- Follow a uniform `BaseAgent` abstract interface.
- Bound strictly to their department's data scope.
- In-database query filtering prevents cross-department data retrieval.
- Never directly query another department's tables without Gateway routing.

### D. Human Approval Workflow State Machine
- Sensitive operations (`payment_execution`, `salary_adjustment`) cannot execute automatically upon LLM recommendation.
- State transitions: `pending` $\rightarrow$ `approved` | `rejected` | `expired`.
- Prevents self-approval (`PREVENT_SELF_APPROVAL=true`).
- Guarantees execution idempotency via `idempotency_key`.

### E. RAG Ingestion & Vector Retrieval
- Supports PDF, DOCX, and TXT files with strict MIME and size checks.
- Chunking preserves document source, page number, and access level.
- Vector retrieval enforces in-database access filters (`WHERE department_id = :dept_id AND access_level IN (:levels)`).
- Chunks from unauthorized departments are filtered out before scoring.

### F. Local Ollama Model Adapter
- Communicates directly with the local host Ollama service (`http://127.0.0.1:11434`).
- Reuses the local pre-installed answer model (`qwen3:8b`).
- Enforces strict local inference: No external fallback or third-party cloud AI requests.

### G. Append-Only Audit Logging
- Logs every authentication attempt, policy evaluation, gateway invocation, document query, and approval lifecycle transition.
- Scoped access: Ordinary employees cannot inspect audit records; managers inspect only their department; auditors and admins inspect system-wide.
- Application-level mutations (`UPDATE` / `DELETE`) on audit records are strictly rejected.
