import sqlite3
import logging
from typing import Optional
from app.db.sqlite import create_connection

logger = logging.getLogger("federated_mesh.db.schema")

CURRENT_SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Schema migration metadata
CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- 1. Departments
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);

-- 2. Users and Roles
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'department_employee',
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    is_active INTEGER NOT NULL DEFAULT 1,
    bio TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_dept ON users(department_id);

-- 3. Department AI Agents
CREATE TABLE IF NOT EXISTS department_agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL UNIQUE REFERENCES departments(id) ON DELETE CASCADE,
    agent_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    system_prompt TEXT DEFAULT '',
    is_enabled INTEGER NOT NULL DEFAULT 1,
    error_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_agents_code ON department_agents(agent_code);

-- 4. Sales: Customers and Opportunities
CREATE TABLE IF NOT EXISTS sales_customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT NOT NULL UNIQUE,
    company_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sales_cust_code ON sales_customers(customer_code);

CREATE TABLE IF NOT EXISTS sales_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER REFERENCES sales_customers(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    client_name TEXT NOT NULL,
    deal_value REAL NOT NULL,
    stage TEXT NOT NULL DEFAULT 'lead',
    probability REAL DEFAULT 0.5,
    lead_source TEXT DEFAULT 'direct',
    needs_finance_approval INTEGER NOT NULL DEFAULT 0,
    finance_status TEXT NOT NULL DEFAULT 'none',
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sales_opp_dept ON sales_opportunities(department_id);
CREATE INDEX IF NOT EXISTS idx_sales_opp_stage ON sales_opportunities(stage);

-- 5. HR: Employees and Leave Records
CREATE TABLE IF NOT EXISTS hr_employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    position TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    leave_balance INTEGER NOT NULL DEFAULT 20,
    salary REAL NOT NULL,
    performance_rating TEXT NOT NULL DEFAULT 'Satisfactory',
    joining_date TEXT DEFAULT '',
    employment_status TEXT NOT NULL DEFAULT 'active',
    is_sensitive INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_hr_emp_code ON hr_employees(employee_code);
CREATE INDEX IF NOT EXISTS idx_hr_emp_dept ON hr_employees(department_id);

CREATE TABLE IF NOT EXISTS hr_leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
    leave_type TEXT NOT NULL,
    days INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'approved',
    start_date TEXT DEFAULT '',
    end_date TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_hr_leaves_emp ON hr_leaves(employee_id);

-- 6. Finance: Vendors, Invoices, Payments, Budgets
CREATE TABLE IF NOT EXISTS finance_vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fin_vendors_code ON finance_vendors(vendor_code);

CREATE TABLE IF NOT EXISTS finance_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER REFERENCES finance_vendors(id) ON DELETE SET NULL,
    invoice_number TEXT NOT NULL UNIQUE,
    client_name TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'sent',
    due_date TIMESTAMP NOT NULL,
    related_opportunity_id INTEGER REFERENCES sales_opportunities(id) ON DELETE SET NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fin_inv_num ON finance_invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_fin_inv_dept ON finance_invoices(department_id);
CREATE INDEX IF NOT EXISTS idx_fin_inv_status ON finance_invoices(status);

CREATE TABLE IF NOT EXISTS finance_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES finance_invoices(id) ON DELETE CASCADE,
    payment_reference TEXT NOT NULL UNIQUE,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL DEFAULT 'wire_transfer',
    status TEXT NOT NULL DEFAULT 'completed',
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fin_pay_ref ON finance_payments(payment_reference);

CREATE TABLE IF NOT EXISTS finance_budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    fiscal_year TEXT NOT NULL,
    allocated_amount REAL NOT NULL,
    spent_amount REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(department_id, fiscal_year)
);

-- 7. Operations: Suppliers, Inventory, Purchase Orders
CREATE TABLE IF NOT EXISTS operations_suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ops_supp_code ON operations_suppliers(supplier_code);

CREATE TABLE IF NOT EXISTS operations_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    reorder_threshold INTEGER NOT NULL DEFAULT 10,
    warehouse_location TEXT NOT NULL,
    supplier_id INTEGER REFERENCES operations_suppliers(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'in_stock',
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ops_inv_sku ON operations_inventory(sku);
CREATE INDEX IF NOT EXISTS idx_ops_inv_dept ON operations_inventory(department_id);

CREATE TABLE IF NOT EXISTS operations_purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT NOT NULL UNIQUE,
    supplier_id INTEGER NOT NULL REFERENCES operations_suppliers(id) ON DELETE RESTRICT,
    sku TEXT NOT NULL REFERENCES operations_inventory(sku) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ordered',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ops_po_num ON operations_purchase_orders(po_number);

-- 8. Documents and Document Chunks (Local Embeddings in SQLite)
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    access_level TEXT NOT NULL DEFAULT 'internal',
    uploaded_by INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'indexed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_docs_dept ON documents(department_id);

CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    access_level TEXT NOT NULL DEFAULT 'internal',
    embedding_blob BLOB,
    embedding_dimension INTEGER DEFAULT 384,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_dept_access ON document_chunks(department_id, access_level);

-- 9. Federation Access Requests
CREATE TABLE IF NOT EXISTS federation_access_requests (
    id TEXT PRIMARY KEY,
    requester_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    requester_department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    requesting_agent TEXT NOT NULL,
    source_department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    business_purpose TEXT NOT NULL,
    requested_fields TEXT NOT NULL,  -- JSON string
    record_identifiers TEXT NOT NULL, -- JSON string
    access_duration_minutes INTEGER NOT NULL DEFAULT 60,
    status TEXT NOT NULL DEFAULT 'PENDING',
    approver_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    decision_reason TEXT,
    approved_fields TEXT,             -- JSON string
    approved_record_ids TEXT,         -- JSON string
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    used_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fed_req_status ON federation_access_requests(status);
CREATE INDEX IF NOT EXISTS idx_fed_req_user ON federation_access_requests(requester_user_id);
CREATE INDEX IF NOT EXISTS idx_fed_req_idemp ON federation_access_requests(idempotency_key);

-- 10. Human Approval Requests
CREATE TABLE IF NOT EXISTS approval_requests (
    id TEXT PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    requester_department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    action_type TEXT NOT NULL,
    target_resource TEXT NOT NULL,
    requested_operation TEXT NOT NULL,
    payload TEXT NOT NULL,            -- JSON string
    status TEXT NOT NULL DEFAULT 'pending',
    approver_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    decision_reason TEXT,
    execution_result TEXT,            -- JSON string
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP,
    executed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_appr_status ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_appr_dept ON approval_requests(requester_department_id);

-- 11. Persistent Conversations and Chat Messages
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conv_dept ON conversations(department_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_role TEXT NOT NULL,        -- 'user' or 'assistant'
    message TEXT NOT NULL,
    intent TEXT,
    routed_departments TEXT,          -- JSON string list
    evidence_json TEXT,               -- JSON string list
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON chat_messages(conversation_id);

-- 12. Security Audit Logs (Append-Only)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    outcome TEXT NOT NULL,            -- 'allow', 'deny', 'error'
    reason TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    actor_email TEXT,
    actor_role TEXT NOT NULL DEFAULT 'system',
    actor_department TEXT NOT NULL DEFAULT 'system',
    resource_id TEXT,
    gateway_decision TEXT,            -- JSON string
    details TEXT                      -- JSON string
);
CREATE INDEX IF NOT EXISTS idx_audit_corr ON audit_logs(correlation_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor_dept ON audit_logs(actor_department);

-- 13. Dataset and Router Metadata
CREATE TABLE IF NOT EXISTS dataset_manifests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_name TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS router_training_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_type TEXT NOT NULL,
    accuracy REAL NOT NULL,
    precision_macro REAL NOT NULL,
    recall_macro REAL NOT NULL,
    f1_macro REAL NOT NULL,
    metrics_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes the SQLite schema idempotently with version tracking.
    Enforces foreign keys, indexes, and tables.
    """
    conn = create_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        
        # Check current schema version
        cursor.execute("SELECT MAX(version) FROM _schema_version;")
        row = cursor.fetchone()
        current_v = row[0] if row and row[0] is not None else 0
        
        if current_v < CURRENT_SCHEMA_VERSION:
            cursor.execute(
                "INSERT INTO _schema_version (version, description) VALUES (?, ?);",
                (CURRENT_SCHEMA_VERSION, f"Initial SQLite schema v{CURRENT_SCHEMA_VERSION}")
            )
            conn.commit()
            logger.info(f"Initialized SQLite database schema to version {CURRENT_SCHEMA_VERSION}.")
        else:
            logger.info(f"SQLite database schema already at version {current_v}.")
    finally:
        conn.close()
