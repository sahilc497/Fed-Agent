# Federated Agentic Mesh — Secure Four-Department Enterprise AI Platform

[![Tests](https://img.shields.io/badge/pytest-54%20passed-brightgreen.svg)]()
[![Model](https://img.shields.io/badge/Local%20LLM-qwen3%3A8b-blue.svg)]()
[![Embeddings](https://img.shields.io/badge/pgvector-384--dim-purple.svg)]()
[![Security](https://img.shields.io/badge/Zero--Trust-Enforced-success.svg)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

A production-grade, local-first enterprise AI platform implementing a **Federated Agentic Mesh** across four independent departments: **Sales**, **Human Resources**, **Finance**, and **Operations**.

The mesh is powered by **one shared local LLM deployment (`qwen3:8b`)** while strictly enforcing **server-side department data isolation**, **admin-controlled Federation Access Requests**, **anti-self-approval controls**, **runtime field-level filtering**, and **immutable audit logging**.

---

## 1. System Architecture

```
                                  ┌───────────────────────────────┐
                                  │      React + TypeScript       │
                                  │   Enterprise Vite Frontend    │
                                  │         (Port 5173)           │
                                  └───────────────┬───────────────┘
                                                  │ REST / JSON (JWT Auth)
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │        FastAPI Backend        │
                                  │   Zero-Trust RBAC Middleware  │
                                  │         (Port 8000)           │
                                  └───────────────┬───────────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                ▼                                ▼
    ┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
    │     Sales AI Agent      │      │       HR AI Agent       │      │     Finance AI Agent    │
    │  (Pipeline, BANT, CRM)  │      │   (Leave, Roster, Org)  │      │  (Invoices, Pay, Wires) │
    └────────────┬────────────┘      └────────────┬────────────┘      └────────────┬────────────┘
                 │                                │                                │
                 └───────────────────────┬────────┴────────────────────────────────┘
                                         ▼
                            ┌─────────────────────────┐
                            │   Operations AI Agent   │
                            │ (Logistics, SKUs, Stock)│
                            └────────────┬────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │      Federation Gateway       │
                         │  - Admin Approval Lifecycle   │
                         │  - Runtime Field Projections  │
                         │  - Anti-Self-Approval Machine │
                         │  - Immediate Grant Revocation │
                         └───────────────┬───────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
    ┌─────────────────────────┐                     ┌─────────────────────────┐
    │   PostgreSQL + pgvector │                     │    Shared Local LLM     │
    │ - Four Department Tables│                     │ - Ollama (Port 11434)   │
    │ - 384-dim Dense Embeds  │                     │ - Model: qwen3:8b       │
    │ - Immutable Audit Trail │                     │ - Zero Cloud Calls      │
    │ - Alembic Migrations    │                     │ - Grounded Evidence Cit.│
    └─────────────────────────┘                     └─────────────────────────┘
```

---

## 2. Core Pillars & Capabilities

1. **Four Autonomous Department Agents**:
   - **Sales Agent (`sales`)**: Client opportunities, BANT criteria, discount thresholds.
   - **HR Agent (`hr`)**: Employee roster, sick leave quotas, parental benefits (with salary masking).
   - **Finance Agent (`finance`)**: Receivables, invoices, dual-authorized wires, audit storage.
   - **Operations Agent (`operations`)**: Warehouse inventory, SKU tracking, reorder levels, logistics SLAs.
2. **One Shared Local LLM (`qwen3:8b`)**:
   - All four agents call a unified singleton Ollama service.
   - Zero external cloud AI dependencies; zero recurring API costs.
   - Pre-LLM authorization: data retrieval occurs strictly before prompt assembly.
3. **Strict Department Data Isolation**:
   - Zero-trust server-side enforcement. Users cannot access cross-department records directly.
   - Negative tests prove prompt injection cannot bypass SQL or pgvector filters.
4. **Admin-Controlled Federation Access Requests**:
   - Formal data-sharing state machine: `PENDING` -> `APPROVED` -> `COMPLETED` (or `REJECTED`, `EXPIRED`, `REVOKED`).
   - Anti-Self-Approval: Requesters cannot approve their own requests.
   - Principle of Least Privilege: Runtime field projection filters out unapproved sensitive attributes.
5. **Admin Governance & Kill-Switch**:
   - Dedicated Admin Dashboard to enable/disable agents, inspect LLM health, and review access requests.
   - Disabled agents instantly refuse new tasks.

---

## 3. Prerequisites

- **OS:** Windows 10/11, macOS, or Linux
- **Python:** 3.10+ (Recommended: Python 3.10.11)
- **Node.js:** v18+ / v20+ / v22+
- **PostgreSQL:** v15+ with `pgvector` extension enabled
- **Ollama:** Installed locally with model `qwen3:8b` (`ollama run qwen3:8b`)

---

## 4. Complete Setup & Installation Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/sahilc497/Fed-Agent.git
cd Fed-Agent
```

### Step 2: Set Up Local Ollama Model
Ensure Ollama is running and has the configured model:
```bash
ollama serve
ollama pull qwen3:8b
```

### Step 3: Configure Backend Environment
```bash
cd backend
cp .env.example .env
```
Ensure your `backend/.env` contains your PostgreSQL credentials:
```ini
APP_NAME="Federated Agentic Mesh"
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/federated_mesh_dev
SYNC_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/federated_mesh_dev
JWT_SECRET_KEY=b2c896503f8485292eb5f3c96644f1074e5033878b66858e8e78077d704ba41c
OLLAMA_BASE_URL=http://127.0.0.1:11434
ANSWER_MODEL=qwen3:8b
OLLAMA_TIMEOUT_SECONDS=120
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

### Step 4: Set Up Python Virtual Environment & Dependencies
```powershell
# From project root:
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies:
pip install -r requirements.txt
```

### Step 5: Run Database Migrations & Seed Data
```powershell
cd backend

# Apply Alembic schema migrations:
alembic upgrade head

# Seed synthetic demo data across all 4 departments:
python scripts/seed_data.py
```

### Step 6: Start Backend Server
```powershell
# Launch FastAPI backend on port 8000:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **API Documentation (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Readiness Check:** [http://127.0.0.1:8000/health/ready](http://127.0.0.1:8000/health/ready)

### Step 7: Set Up and Start Frontend
Open a new terminal window:
```powershell
cd frontend
npm install
npm run dev
```
- **Application URL:** [http://localhost:5173](http://localhost:5173)

---

## 5. Demonstration Credentials

All seeded demo accounts use the standard password: `MeshSecure2026!`

| Department | Role | Email | Password | Allowed Scope |
| :--- | :--- | :--- | :--- | :--- |
| **System** | **Security Admin** | `admin@mesh.enterprise.internal` | `MeshSecure2026!` | Global review, Federation Approvals, Agent Enable/Disable |
| **System** | **Compliance Auditor** | `auditor@mesh.enterprise.internal` | `MeshSecure2026!` | Read-only tamper-evident audit logs |
| **Sales** | **Sales Head** | `sales.manager@mesh.enterprise.internal` | `MeshSecure2026!` | Sales opportunities & pipeline CRM |
| **Sales** | **Sales Rep** | `sales.rep@mesh.enterprise.internal` | `MeshSecure2026!` | Sales only; submits cross-dept federation requests |
| **HR** | **HR Director** | `hr.manager@mesh.enterprise.internal` | `MeshSecure2026!` | Full employee records & PTO |
| **HR** | **HR Specialist** | `hr.specialist@mesh.enterprise.internal` | `MeshSecure2026!` | Employee directory (salaries masked) |
| **Finance** | **Controller** | `finance.manager@mesh.enterprise.internal` | `MeshSecure2026!` | Invoices, receivables & wire authorizations |
| **Finance** | **Financial Analyst**| `finance.analyst@mesh.enterprise.internal` | `MeshSecure2026!` | Invoices & financial ledgers |
| **Operations** | **Operations Lead** | `operations.lead@mesh.enterprise.internal` | `MeshSecure2026!` | Warehouse stock, SKUs, fulfillment |

---

## 6. Verification & Automated Test Suite

### 1. Run Complete Backend Test Suite (54 Tests)
```powershell
cd backend
pytest tests -v
```
**Coverage:** 54/54 passed (100%):
- All 4 departments & agents registration
- Shared local LLM client reuse
- 4-way cross-department isolation negative tests
- Federation Access Request lifecycle & anti-self-approval
- Revocation & expiry enforcement
- Prompt injection resistance & LLM failure fail-closed behavior
- Semantic RAG vector isolation

### 2. Run End-to-End Mesh Verification Script
```powershell
cd backend
python scripts/verify_four_mesh_e2e.py
```
Validates the complete live lifecycle (Health -> 4 Agents -> Ops Inventory -> Cross-Dept 403 block -> Admin approval -> Field filtering -> Grant revocation).

### 3. Build Frontend Production Assets
```powershell
cd frontend
npm run build
```
Typechecks and packages client distribution bundle with zero TypeScript errors.

---

## 7. Project Structure

```
Fed-Agent/
├── backend/
│   ├── alembic/                 # Reversible database migrations (001, 002)
│   ├── app/
│   │   ├── agents/              # Sales, HR, Finance, Operations agent implementations
│   │   ├── api/v1/              # REST routes (auth, chat, agents, federation, depts)
│   │   ├── core/                # Config, JWT security, custom exceptions
│   │   ├── db/models/           # SQLAlchemy models (User, Dept, Agent, FederationRequest)
│   │   ├── gateway/             # Zero-Trust Federation Gateway & policy rules
│   │   ├── orchestrator/        # Multi-agent intent classification & dispatch
│   │   ├── rag/                 # Sentence-transformers embedding & pgvector retrieval
│   │   ├── repositories/        # Database access layers
│   │   ├── schemas/             # Pydantic validation schemas
│   │   └── services/            # Shared Ollama service, Federation service, Agent service
│   ├── scripts/                 # Seed data, E2E verification, admin setup
│   └── tests/                   # 54 automated pytest tests
├── frontend/
│   ├── src/
│   │   ├── api/                 # Typed API client for mesh backend
│   │   ├── pages/               # Dashboard, Chat, Approvals & Federation, Dept Views
│   │   └── context/             # AuthContext with token management
│   └── package.json
├── requirements.txt             # Backend Python dependencies
├── .gitignore                   # Ignores venv, node_modules, cache, and secrets
└── README.md                    # Project documentation
```

---

## 8. License

This project is licensed under the MIT License.
