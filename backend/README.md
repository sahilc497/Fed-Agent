# Federated Agentic Mesh — Secure Multi-Agent Enterprise AI Backend

A local-first enterprise AI system enabling employees from different departments (Sales, HR, Finance) to interact via a unified conversational AI interface while maintaining strict department data isolation, zero-trust authorization boundaries, human approval controls, and local-only LLM inference through Ollama.

---

## 1. Key Features

- **Unified Chat Interface:** Multi-department intelligent intent routing across Sales, HR, and Finance.
- **Department Isolation:** In-database query filtering guarantees no agent can directly query private tables or vector memory of another department.
- **Federation Gateway:** Strict security boundary governing all cross-department requests with explicit field whitelisting and forbidden field rejection.
- **Human Approval State Machine:** Mandates human authorization for high-impact actions (e.g. payments, sensitive changes) with idempotency controls and self-approval prevention.
- **Local-Only Ollama Inference:** Reuses the verified installed `qwen3:8b` model. No proprietary company data is ever sent to external cloud AI APIs.
- **Append-Only Audit Logging:** Immutable application-level audit logging for all authentication attempts, policy evaluations, gateway queries, and approval decisions.
- **Pluggable Local RAG Embeddings:** Multi-format document ingestion (PDF, DOCX, TXT) with access-level filtering and configurable embedding engines (`local_hash`, `ollama`, `sentence_transformers`).

---

## 2. System Requirements

- **Operating System:** Windows 10/11 (64-bit).
- **Python:** Python 3.10.x.
- **Database:** PostgreSQL 15+ (with native trust/password authentication on port 5432).
- **AI Runtime:** Ollama (with verified local model `qwen3:8b` installed).
- **Hardware:** 16 GB RAM (compatible with local 8B quantized models on integrated graphics).

---

## 3. Quickstart & Windows PowerShell Setup

### Step 1: Open PowerShell in the Backend Directory
```powershell
Set-Location d:\AgenticAI\Fedral-Agent\backend
```

### Step 2: Create & Activate Virtual Environment
```powershell
# Create venv with Python 3.10
python -m venv ..\venv

# Activate venv
..\venv\Scripts\Activate.ps1
```

### Step 3: Install Verified Dependencies
```powershell
pip install -r ..\requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
The `.env` file is pre-configured for local development with:
- `OLLAMA_BASE_URL=http://127.0.0.1:11434`
- `ANSWER_MODEL=qwen3:8b`
- `DATABASE_URL=postgresql+asyncpg://postgres@127.0.0.1:5432/federated_mesh_dev`
- `SYNC_DATABASE_URL=postgresql+psycopg2://postgres@127.0.0.1:5432/federated_mesh_dev`
- `EMBEDDING_PROVIDER=local_hash`

### Step 5: Verify Local Ollama AI Model
Ensure Ollama is running and inspect the model:
```powershell
ollama list
```
Verify `qwen3:8b` is present. To test local generation:
```powershell
python scripts/test_llm.py
```

### Step 6: Apply Alembic Migrations
Alembic migrations generate and maintain the complete database schema with upgrade and downgrade capabilities:
```powershell
alembic upgrade head
```

### Step 7: Seed Idempotent Synthetic Enterprise Data
Populate realistic synthetic sales deals, confidential HR employee records, invoices, and internal knowledge documents:
```powershell
python scripts/seed_data.py
```

### Step 8: User Provisioning & Password Management
Create an administrator or reset any user account password via CLI without exposing credentials in source code:
```powershell
# Provision new Administrator:
python scripts/create_admin.py admin@mesh.enterprise.internal <new_password> "System Administrator"

# Reset account password:
python scripts/reset_password.py sales.rep@mesh.enterprise.internal <new_password>
```

---

## 4. Running the Backend Server

Start the FastAPI application using Uvicorn:
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive API Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Readiness Dependency Probe:** [http://127.0.0.1:8000/health/ready](http://127.0.0.1:8000/health/ready)

---

## 5. Running the Automated Test Suite

Run the complete test suite covering all 33 functional, security, isolation, and authorization test cases:
```powershell
pytest tests -v
```

All 33 tests pass with 100% success:
- `test_health.py`: Liveness and database/Ollama readiness probes.
- `test_auth.py`: Argon2id password verification, JWT issuance, secret shielding.
- `test_permissions.py`: Deny-by-default matrix, audit immutability, salary restrictions.
- `test_department_isolation.py`: Cross-department direct access denial, role elevation prevention.
- `test_gateway.py`: Federation gateway contracts, field filtering, unauthorized bridge rejection.
- `test_approvals.py`: Approval state machine, self-approval prevention, duplicate execution guards.
- `test_rag.py`: Document ingestion, access-level chunking, vector isolation.
- `test_ollama.py`: Local model verification, offline failure handling.
- `test_scenarios.py`: End-to-end Demonstration Scenarios A through G.
- `test_live_cross_dept_security.py`: Direct document ID isolation, cross-department chat denial, and audit log persistence.

---

## 6. Embedding Architecture & Options

The backend provides a pluggable embedding interface (`BaseEmbeddingService`):
1. **`local_hash` (Default):** Zero-download 384-dimensional deterministic feature-hashing vectorizer. Ideal for local development, offline runs, and automated testing without external weight downloads.
2. **`ollama`:** Uses the local Ollama server's embedding API. Requires Ollama to be started with an embedding model (e.g. `ollama pull nomic-embed-text`).
3. **`sentence_transformers`:** High-accuracy local neural embeddings via Hugging Face Sentence Transformers (e.g., `all-MiniLM-L6-v2`). Fails clearly if local weights are missing and `ALLOW_MODEL_DOWNLOADS=false`.

---

## 7. Supported Demonstration Scenarios

- **Scenario A (HR Question):** Authorized HR employee asks about leave policy; retrieved from authorized HR documents.
- **Scenario B (Sales to Finance):** Sales employee asks which opportunities are awaiting Finance approval; routed via the Federation Gateway with field filtering.
- **Scenario C (Restricted Salary):** Sales employee asks for an employee's salary; strictly denied with zero information leakage.
- **Scenario D (Sensitive Financial Action):** User requests an invoice wire transfer; triggers a human approval request; action remains pending until manager authorization.
- **Scenario E (Multi-Department Question):** User asks a question spanning deals and invoice statuses; Orchestrator coordinates authorized agents and combines evidence.
- **Scenario F (Prompt Injection Defense):** Malicious prompt instructs model to ignore security rules and dump executive compensation; denied by policy layer.
- **Scenario G (Unknown Request):** Ambiguous or out-of-scope query; returns safe clarification request rather than inventing facts.

---

## 8. Security Limitations & Known Gaps

1. **Database Superuser Boundary:** Application-level audit logging is append-only through API and repository logic. However, an external privileged database administrator with direct SQL access could theoretically modify PostgreSQL tables directly.
2. **Operations Department Deferred:** Intent routing recognizes Operations as a planned Phase 2 capability and safely returns a deferred notice without architectural changes.
3. **Local Vector Acceleration:** The system uses 384-dimensional cosine similarity embeddings in PostgreSQL. If the native `pgvector` C extension is compiled in PostgreSQL, an HNSW vector index can be added with zero changes to the application repository interface.
