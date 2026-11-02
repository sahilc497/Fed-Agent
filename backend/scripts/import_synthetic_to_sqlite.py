import os
import sys
import json
import logging
from pathlib import Path

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db.sqlite import create_connection, db_transaction
from app.db.schema import init_db
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("import_synthetic")


def import_all():
    init_db()
    data_dir = BASE_DIR / "data"
    gen_dir = data_dir / "generated"

    with db_transaction() as conn:
        logger.info("Importing departments...")
        departments = [
            (1, "sales", "Sales Department", "Enterprise customer acquisition, pipeline management, and contract negotiation."),
            (2, "hr", "Human Resources", "Talent acquisition, employee relations, payroll, benefits, and policy administration."),
            (3, "finance", "Finance & Accounting", "Financial planning, invoice management, payments, auditing, and fiscal compliance."),
            (4, "operations", "Operations Department", "Supply chain, inventory tracking, warehouse logistics, fulfillment, and facilities management.")
        ]
        for dept in departments:
            conn.execute(
                """INSERT INTO departments (id, code, name, description)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(code) DO UPDATE SET name=excluded.name, description=excluded.description;""",
                dept
            )

        logger.info("Importing core users...")
        users = [
            ("admin@mesh.enterprise.internal", "Sarah Connor (Admin)", 3, "admin", "System Administrator with global federation control"),
            ("sales.manager@mesh.enterprise.internal", "Elena Rostova (Sales Head)", 1, "department_manager", "Sales Department Director"),
            ("sales.rep@mesh.enterprise.internal", "David Miller (Account Exec)", 1, "department_employee", "Sales Representative"),
            ("hr.manager@mesh.enterprise.internal", "Rachel Vance (HR Director)", 2, "department_manager", "Human Resources Director"),
            ("hr.specialist@mesh.enterprise.internal", "Tom Holland (HR Specialist)", 2, "department_employee", "Human Resources Specialist"),
            ("finance.manager@mesh.enterprise.internal", "Arthur Dent (Controller)", 3, "department_manager", "Corporate Controller"),
            ("finance.analyst@mesh.enterprise.internal", "Gwen Stacy (Financial Analyst)", 3, "department_employee", "Financial Planning Analyst"),
            ("operations.manager@mesh.enterprise.internal", "Victor Stone (Operations Director)", 4, "department_manager", "Operations Director"),
            ("operations.lead@mesh.enterprise.internal", "Chloe Decker (Logistics Lead)", 4, "department_employee", "Warehouse & Logistics Lead")
        ]
        default_pwd_hash = hash_password("MeshSecure2026!")
        for email, full_name, dept_id, role, bio in users:
            conn.execute(
                """INSERT INTO users (email, hashed_password, full_name, department_id, role, is_active, bio)
                   VALUES (?, ?, ?, ?, ?, 1, ?)
                   ON CONFLICT(email) DO UPDATE SET full_name=excluded.full_name, role=excluded.role, bio=excluded.bio;""",
                (email, default_pwd_hash, full_name, dept_id, role, bio)
            )

        logger.info("Importing department agents...")
        agents = [
            (1, "sales", "Sales Agent", "Handles client opportunities, pipeline BANT criteria, and proposals.", "You are the autonomous Sales Agent."),
            (2, "hr", "HR Agent", "Handles employee roster, leave balances, benefits, and procedures.", "You are the autonomous HR Agent."),
            (3, "finance", "Finance Agent", "Handles invoices, receivables, accounts payable, and dual-authorized wires.", "You are the autonomous Finance Agent."),
            (4, "operations", "Operations Agent", "Handles warehouse logistics, SKUs, inventory, and supply chain fulfillment.", "You are the autonomous Operations Agent.")
        ]
        for dept_id, code, name, desc, prompt in agents:
            conn.execute(
                """INSERT INTO department_agents (department_id, agent_code, name, description, system_prompt, is_enabled)
                   VALUES (?, ?, ?, ?, ?, 1)
                   ON CONFLICT(agent_code) DO UPDATE SET name=excluded.name, description=excluded.description;""",
                (dept_id, code, name, desc, prompt)
            )

        # 1. Sales: Customers and Opportunities
        cust_file = gen_dir / "sales" / "sales_customers.json"
        if cust_file.exists():
            with open(cust_file, "r", encoding="utf-8") as f:
                customers = json.load(f)
            logger.info(f"Importing {len(customers)} synthetic sales customers...")
            for c in customers:
                conn.execute(
                    """INSERT INTO sales_customers (id, customer_code, company_name, industry, contact_name, contact_email, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(customer_code) DO NOTHING;""",
                    (c["id"], c["customer_code"], c["company_name"], c["industry"], c["contact_name"], c["contact_email"], c["status"], c["created_at"])
                )

        opps_file = gen_dir / "sales" / "sales_opportunities.json"
        if opps_file.exists():
            with open(opps_file, "r", encoding="utf-8") as f:
                opps = json.load(f)
            logger.info(f"Importing {len(opps)} synthetic sales opportunities...")
            for o in opps:
                conn.execute(
                    """INSERT INTO sales_opportunities (
                        id, customer_id, title, client_name, deal_value, stage, probability,
                        lead_source, needs_finance_approval, finance_status, owner_id, department_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO NOTHING;""",
                    (
                        o["id"], o["customer_id"], o["title"], o["client_name"], o["deal_value"], o["stage"],
                        o["probability"], o["lead_source"], 1 if o["needs_finance_approval"] else 0,
                        o["finance_status"], o["owner_id"], o["department_id"], o["created_at"], o["updated_at"]
                    )
                )

        # 2. HR: Employees and Leaves
        emp_file = gen_dir / "hr" / "hr_employees.json"
        if emp_file.exists():
            with open(emp_file, "r", encoding="utf-8") as f:
                employees = json.load(f)
            logger.info(f"Importing {len(employees)} synthetic HR employees...")
            for e in employees:
                conn.execute(
                    """INSERT INTO hr_employees (
                        id, employee_code, full_name, position, department_id, leave_balance,
                        salary, performance_rating, joining_date, employment_status, is_sensitive, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(employee_code) DO NOTHING;""",
                    (
                        e["id"], e["employee_code"], e["full_name"], e["position"], e["department_id"],
                        e["leave_balance"], e["salary"], e["performance_rating"], e["joining_date"],
                        e["employment_status"], 1 if e["is_sensitive"] else 0, e["created_at"]
                    )
                )

        leaves_file = gen_dir / "hr" / "hr_leaves.json"
        if leaves_file.exists():
            with open(leaves_file, "r", encoding="utf-8") as f:
                leaves = json.load(f)
            logger.info(f"Importing {len(leaves)} synthetic HR leave records...")
            for l in leaves:
                conn.execute(
                    """INSERT INTO hr_leaves (id, employee_id, leave_type, days, status, start_date, end_date, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO NOTHING;""",
                    (l["id"], l["employee_id"], l["leave_type"], l["days"], l["status"], l["start_date"], l["end_date"], l["created_at"])
                )

        # 3. Finance: Vendors, Invoices, Payments
        ven_file = gen_dir / "finance" / "finance_vendors.json"
        if ven_file.exists():
            with open(ven_file, "r", encoding="utf-8") as f:
                vendors = json.load(f)
            logger.info(f"Importing {len(vendors)} synthetic finance vendors...")
            for v in vendors:
                conn.execute(
                    """INSERT INTO finance_vendors (id, vendor_code, name, category, contact_email, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(vendor_code) DO NOTHING;""",
                    (v["id"], v["vendor_code"], v["name"], v["category"], v["contact_email"], v["status"], v["created_at"])
                )

        inv_file = gen_dir / "finance" / "finance_invoices.json"
        if inv_file.exists():
            with open(inv_file, "r", encoding="utf-8") as f:
                invoices = json.load(f)
            logger.info(f"Importing {len(invoices)} synthetic finance invoices...")
            for inv in invoices:
                conn.execute(
                    """INSERT INTO finance_invoices (
                        id, vendor_id, invoice_number, client_name, amount, status,
                        due_date, related_opportunity_id, department_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(invoice_number) DO NOTHING;""",
                    (
                        inv["id"], inv["vendor_id"], inv["invoice_number"], inv["client_name"], inv["amount"],
                        inv["status"], inv["due_date"], inv["related_opportunity_id"], inv["department_id"], inv["created_at"]
                    )
                )

        pay_file = gen_dir / "finance" / "finance_payments.json"
        if pay_file.exists():
            with open(pay_file, "r", encoding="utf-8") as f:
                payments = json.load(f)
            logger.info(f"Importing {len(payments)} synthetic finance payments...")
            for p in payments:
                conn.execute(
                    """INSERT INTO finance_payments (id, invoice_id, payment_reference, amount, payment_method, status, department_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(payment_reference) DO NOTHING;""",
                    (p["id"], p["invoice_id"], p["payment_reference"], p["amount"], p["payment_method"], p["status"], p["department_id"], p["created_at"])
                )

        # 4. Operations: Suppliers, Inventory, POs
        sup_file = gen_dir / "operations" / "operations_suppliers.json"
        if sup_file.exists():
            with open(sup_file, "r", encoding="utf-8") as f:
                suppliers = json.load(f)
            logger.info(f"Importing {len(suppliers)} synthetic operations suppliers...")
            for s in suppliers:
                conn.execute(
                    """INSERT INTO operations_suppliers (id, supplier_code, name, contact_email, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(supplier_code) DO NOTHING;""",
                    (s["id"], s["supplier_code"], s["name"], s["contact_email"], s["status"], s["created_at"])
                )

        inv_ops_file = gen_dir / "operations" / "operations_inventory.json"
        if inv_ops_file.exists():
            with open(inv_ops_file, "r", encoding="utf-8") as f:
                items = json.load(f)
            logger.info(f"Importing {len(items)} synthetic operations inventory items...")
            for it in items:
                conn.execute(
                    """INSERT INTO operations_inventory (
                        id, sku, item_name, category, quantity_on_hand, reserved_quantity,
                        reorder_threshold, warehouse_location, supplier_id, status, department_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sku) DO NOTHING;""",
                    (
                        it["id"], it["sku"], it["item_name"], it["category"], it["quantity_on_hand"],
                        it["reserved_quantity"], it["reorder_threshold"], it["warehouse_location"],
                        it["supplier_id"], it["status"], it["department_id"], it["created_at"]
                    )
                )

        po_file = gen_dir / "operations" / "operations_purchase_orders.json"
        if po_file.exists():
            with open(po_file, "r", encoding="utf-8") as f:
                pos = json.load(f)
            logger.info(f"Importing {len(pos)} synthetic operations purchase orders...")
            for po in pos:
                conn.execute(
                    """INSERT INTO operations_purchase_orders (id, po_number, supplier_id, sku, quantity, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(po_number) DO NOTHING;""",
                    (po["id"], po["po_number"], po["supplier_id"], po["sku"], po["quantity"], po["status"], po["created_at"])
                )

        # 5. Manifest metadata
        manifest_file = data_dir / "manifests" / "dataset_manifest.json"
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                mf = json.load(f)
            for dept_name in ["sales", "hr", "finance", "operations"]:
                d_mf = mf.get(dept_name, {})
                c_sum = d_mf.get("opportunities_checksum") or d_mf.get("employees_checksum") or d_mf.get("invoices_checksum") or d_mf.get("inventory_checksum") or "n/a"
                r_cnt = d_mf.get("opportunities_count") or d_mf.get("employees_count") or d_mf.get("invoices_count") or d_mf.get("inventory_count") or 0
                conn.execute(
                    """INSERT INTO dataset_manifests (dataset_name, version, record_count, checksum)
                       VALUES (?, '1.0.0', ?, ?)
                       ON CONFLICT(dataset_name) DO UPDATE SET record_count=excluded.record_count, checksum=excluded.checksum;""",
                    (f"{dept_name}_synthetic_v1", r_cnt, c_sum)
                )

    logger.info("Synthetic dataset successfully imported into SQLite.")


if __name__ == "__main__":
    import_all()
