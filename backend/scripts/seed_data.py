import os
import sys
import asyncio
import datetime

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.db.models import (
    Department,
    User,
    PermissionPolicy,
    SalesOpportunity,
    HREmployeeRecord,
    HRLeaveRecord,
    FinanceInvoice,
    FinancePayment,
    OperationsInventoryItem,
    Document,
    DocumentChunk,
    ApprovalRequest,
    AuditLog,
    DepartmentAgent,
    FederationAccessRequest
)
from app.rag.embeddings import get_embedding_service


async def seed_all():
    async with AsyncSessionLocal() as session:
        print("Starting idempotent synthetic data seeding for 4 departments...")

        # 1. Departments (Sales, HR, Finance, Operations)
        departments_data = [
            {"code": "sales", "name": "Sales Department", "description": "Enterprise customer acquisition, pipeline management, and contract negotiation."},
            {"code": "hr", "name": "Human Resources", "description": "Talent acquisition, employee relations, payroll, benefits, and policy administration."},
            {"code": "finance", "name": "Finance & Accounting", "description": "Financial planning, invoice management, payments, auditing, and fiscal compliance."},
            {"code": "operations", "name": "Operations Department", "description": "Supply chain, inventory tracking, warehouse logistics, fulfillment, and facilities management."}
        ]

        dept_map = {}
        for d in departments_data:
            stmt = select(Department).where(Department.code == d["code"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                dept_obj = Department(**d)
                session.add(dept_obj)
                await session.flush()
                dept_map[d["code"]] = dept_obj
                print(f"Created department: {d['name']}")
            else:
                dept_map[d["code"]] = existing
                print(f"Department exists: {d['name']}")

        # 2. Users (Admin, Managers, Employees, Auditor across all 4 departments)
        users_data = [
            {"email": "admin@mesh.enterprise.internal", "full_name": "Sarah Connor (Admin)", "dept": "finance", "role": "admin"},
            {"email": "auditor@mesh.enterprise.internal", "full_name": "Marcus Aurelius (Auditor)", "dept": "finance", "role": "auditor"},
            {"email": "sales.manager@mesh.enterprise.internal", "full_name": "Elena Rostova (Sales Head)", "dept": "sales", "role": "department_manager"},
            {"email": "sales.rep@mesh.enterprise.internal", "full_name": "David Miller (Account Exec)", "dept": "sales", "role": "department_employee"},
            {"email": "hr.manager@mesh.enterprise.internal", "full_name": "Rachel Vance (HR Director)", "dept": "hr", "role": "department_manager"},
            {"email": "hr.specialist@mesh.enterprise.internal", "full_name": "Tom Holland (HR Specialist)", "dept": "hr", "role": "department_employee"},
            {"email": "finance.manager@mesh.enterprise.internal", "full_name": "Arthur Dent (Controller)", "dept": "finance", "role": "department_manager"},
            {"email": "finance.analyst@mesh.enterprise.internal", "full_name": "Gwen Stacy (Financial Analyst)", "dept": "finance", "role": "department_employee"},
            {"email": "operations.manager@mesh.enterprise.internal", "full_name": "Victor Stone (Operations Director)", "dept": "operations", "role": "department_manager"},
            {"email": "operations.lead@mesh.enterprise.internal", "full_name": "Chloe Decker (Logistics Lead)", "dept": "operations", "role": "department_employee"},
        ]

        user_map = {}
        for u in users_data:
            stmt = select(User).where(User.email == u["email"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                u_obj = User(
                    email=u["email"],
                    hashed_password=hash_password("MeshSecure2026!"),
                    full_name=u["full_name"],
                    department_id=dept_map[u["dept"]].id,
                    role=u["role"],
                    is_active=True
                )
                session.add(u_obj)
                await session.flush()
                user_map[u["email"]] = u_obj
                print(f"Created user: {u['email']}")
            else:
                user_map[u["email"]] = existing

        # 3. Sales Opportunities
        sales_data = [
            ("Apex Global Cloud Migration", "Apex Corp", 450000.0, "proposal", True, "pending"),
            ("Quantum Data Warehouse License", "Quantum Logistics", 185000.0, "qualified", True, "pending"),
            ("Titan Security Appliance Order", "Titan Heavy Industries", 720000.0, "proposal", True, "pending"),
            ("BlueSky CRM Enterprise Upgrade", "BlueSky Aviation", 95000.0, "closed_won", False, "approved"),
            ("Nordic Retail Point of Sale", "Nordic Supermarkets", 310000.0, "closed_won", False, "approved"),
            ("Vanguard AI Mesh Pilot", "Vanguard Financial", 120000.0, "lead", False, "none"),
            ("Zenith Telematics Rollout", "Zenith Mobility", 240000.0, "proposal", True, "pending"),
            ("Solaris Energy Monitoring Platform", "Solaris Power", 530000.0, "proposal", True, "pending"),
            ("Helios Microservices Modernization", "Helios Labs", 85000.0, "qualified", False, "none"),
            ("Pinnacle Healthcare Telehealth Suite", "Pinnacle Health", 640000.0, "closed_won", False, "approved"),
            ("Orion Logistics Fleet Tracking", "Orion Global", 195000.0, "lead", False, "none"),
            ("Cascade Water Utility Smart Meters", "Cascade Utilities", 410000.0, "proposal", True, "pending"),
            ("Summit Biotech Genomics Pipeline", "Summit Pharma", 890000.0, "proposal", True, "pending"),
            ("Aurora Media Streaming Architecture", "Aurora Media", 150000.0, "closed_won", False, "approved"),
            ("Atlas Automotive Diagnostic Edge", "Atlas Motors", 375000.0, "proposal", True, "pending"),
        ]

        for title, client, val, stage, needs_fin, fin_st in sales_data:
            stmt = select(SalesOpportunity).where(SalesOpportunity.title == title)
            if not (await session.execute(stmt)).scalar_one_or_none():
                session.add(SalesOpportunity(
                    title=title,
                    client_name=client,
                    deal_value=val,
                    stage=stage,
                    needs_finance_approval=needs_fin,
                    finance_status=fin_st,
                    owner_id=user_map["sales.rep@mesh.enterprise.internal"].id,
                    department_id=dept_map["sales"].id
                ))

        # 4. HR Employee Records
        hr_data = [
            ("EMP-1001", "Alice Jenkins", "Staff Software Engineer", 18, 145000.0, "Exceeds Expectations"),
            ("EMP-1002", "Robert Chen", "Senior Frontend Developer", 15, 128000.0, "Satisfactory"),
            ("EMP-1003", "Maria Gonzalez", "Principal Security Architect", 22, 175000.0, "Exceeds Expectations"),
            ("EMP-1004", "Daniel Kim", "Lead Cloud Infrastructure Engineer", 14, 152000.0, "Satisfactory"),
            ("EMP-1005", "Sophia Patel", "Senior Machine Learning Engineer", 20, 160000.0, "Exceeds Expectations"),
            ("EMP-1006", "Lucas Wright", "DevOps Engineer", 16, 115000.0, "Satisfactory"),
            ("EMP-1007", "Hannah Abbott", "Technical Product Manager", 19, 138000.0, "Satisfactory"),
            ("EMP-1008", "James Wilson", "QA Automation Lead", 17, 118000.0, "Satisfactory"),
            ("EMP-1009", "Fatima Al-Mansoor", "Data Governance Specialist", 21, 130000.0, "Exceeds Expectations"),
            ("EMP-1010", "Oliver Brown", "Systems Administrator", 12, 102000.0, "Needs Improvement"),
            ("EMP-1011", "Chloe Martin", "UI/UX Design Director", 20, 142000.0, "Exceeds Expectations"),
            ("EMP-1012", "Ethan Taylor", "Backend Go Developer", 15, 125000.0, "Satisfactory"),
            ("EMP-1013", "Grace Hopper Jr.", "Distributed Systems Architect", 25, 195000.0, "Exceeds Expectations"),
            ("EMP-1014", "Alexander Reed", "Database Reliability Engineer", 18, 134000.0, "Satisfactory"),
            ("EMP-1015", "Mia Zhang", "Technical Compliance Officer", 16, 122000.0, "Satisfactory"),
        ]

        for code, name, pos, leaves, sal, rating in hr_data:
            stmt = select(HREmployeeRecord).where(HREmployeeRecord.employee_code == code)
            if not (await session.execute(stmt)).scalar_one_or_none():
                session.add(HREmployeeRecord(
                    employee_code=code,
                    full_name=name,
                    position=pos,
                    department_id=dept_map["hr"].id,
                    leave_balance=leaves,
                    salary=sal,
                    performance_rating=rating,
                    is_sensitive=True
                ))

        # 5. Finance Invoices
        finance_data = [
            ("INV-2026-001", "Apex Corp", 112500.0, "sent", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=15)),
            ("INV-2026-002", "Titan Heavy Industries", 180000.0, "overdue", datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=24)),
            ("INV-2026-003", "BlueSky Aviation", 95000.0, "paid", datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)),
            ("INV-2026-004", "Nordic Supermarkets", 77500.0, "overdue", datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=35)),
            ("INV-2026-005", "Quantum Logistics", 46250.0, "sent", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=20)),
            ("INV-2026-006", "Solaris Power", 132500.0, "pending_approval", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=45)),
            ("INV-2026-007", "Zenith Mobility", 60000.0, "sent", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=12)),
            ("INV-2026-008", "Pinnacle Health", 160000.0, "paid", datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=5)),
            ("INV-2026-009", "Cascade Utilities", 102500.0, "draft", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=60)),
            ("INV-2026-010", "Summit Pharma", 222500.0, "overdue", datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=15)),
            ("INV-2026-011", "Aurora Media", 150000.0, "paid", datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)),
            ("INV-2026-012", "Atlas Motors", 93750.0, "pending_approval", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)),
            ("INV-2026-013", "Helios Labs", 85000.0, "sent", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=18)),
            ("INV-2026-014", "Orion Global", 48750.0, "sent", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=25)),
            ("INV-2026-015", "Vanguard Financial", 120000.0, "sent", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)),
        ]

        for inv_num, client, amt, st, due in finance_data:
            stmt = select(FinanceInvoice).where(FinanceInvoice.invoice_number == inv_num)
            if not (await session.execute(stmt)).scalar_one_or_none():
                session.add(FinanceInvoice(
                    invoice_number=inv_num,
                    client_name=client,
                    amount=amt,
                    status=st,
                    due_date=due,
                    department_id=dept_map["finance"].id
                ))

        # 6. Operations Inventory Items (15+ synthetic records)
        ops_inventory_data = [
            ("SKU-OPS-001", "Enterprise Server Rack 42U", "Data Center Hardware", 45, 10, "Warehouse North - Bay 1A", "in_stock"),
            ("SKU-OPS-002", "10GbE Optical Transceiver SFP+", "Networking", 320, 50, "Warehouse North - Bay 2B", "in_stock"),
            ("SKU-OPS-003", "Cat6A Shielded Spool 1000ft", "Cabling", 18, 25, "Warehouse North - Bay 3C", "low_stock"),
            ("SKU-OPS-004", "Heavy-Duty Euro Pallets (Wood)", "Packaging", 240, 40, "Warehouse Central - Yard A", "in_stock"),
            ("SKU-OPS-005", "High-Velocity Server Cooling Fan 120mm", "Hardware", 110, 30, "Warehouse North - Bay 1B", "in_stock"),
            ("SKU-OPS-006", "Li-Ion UPS Backup Battery Pack", "Power Systems", 12, 15, "Warehouse South - Secure Room", "low_stock"),
            ("SKU-OPS-007", "Industrial RFID Asset Tracking Tags (Pack 500)", "Inventory Tech", 85, 20, "Warehouse North - Bay 4A", "in_stock"),
            ("SKU-OPS-008", "Wireless Ruggedized Barcode Scanner", "Equipment", 35, 10, "Warehouse Central - Tool Crib", "in_stock"),
            ("SKU-OPS-009", "Thermal Direct Shipping Label Rolls", "Packaging", 450, 100, "Warehouse Central - Packing Stn", "in_stock"),
            ("SKU-OPS-010", "LC-LC Duplex Single-Mode Fiber 5m", "Cabling", 90, 20, "Warehouse North - Bay 2C", "in_stock"),
            ("SKU-OPS-011", "Horizontal 1U Cable Management Duct", "Rack Accessories", 65, 15, "Warehouse North - Bay 1C", "in_stock"),
            ("SKU-OPS-012", "Hydraulic Pallet Jack 5500lb", "Material Handling", 8, 3, "Warehouse Central - Floor", "in_stock"),
            ("SKU-OPS-013", "Class-2 Fall Protection Safety Harness", "Safety Gear", 40, 10, "Warehouse South - Safety Stn", "in_stock"),
            ("SKU-OPS-014", "Anti-Static ESD Workstation Mat", "Assembly", 28, 10, "Warehouse North - Assembly Bay", "in_stock"),
            ("SKU-OPS-015", "Heavy Duty Industrial Shrink Film 80 Gauge", "Packaging", 0, 15, "Warehouse Central - Packing Stn", "out_of_stock"),
        ]

        for sku, name, cat, qty, reorder, loc, status_val in ops_inventory_data:
            stmt = select(OperationsInventoryItem).where(OperationsInventoryItem.sku == sku)
            if not (await session.execute(stmt)).scalar_one_or_none():
                session.add(OperationsInventoryItem(
                    sku=sku,
                    item_name=name,
                    category=cat,
                    quantity_on_hand=qty,
                    reorder_threshold=reorder,
                    warehouse_location=loc,
                    status=status_val,
                    department_id=dept_map["operations"].id
                ))

        # 7. Department Agents Configuration (All 4 Departments)
        agent_data = [
            ("sales", "Sales Agent", "Enterprise pipeline, deal qualification, BANT scoring, CRM integration", "You are the Sales Department Agent. You answer sales pipeline, client deal, and revenue questions based solely on authorized sales evidence."),
            ("hr", "HR Agent", "Employee relations, paid time off, benefits, performance reviews", "You are the HR Department Agent. You answer employee policy, leave allocation, and roster questions based solely on authorized HR evidence."),
            ("finance", "Finance Agent", "Invoices, wire disbursements, accounts receivable, expense policies", "You are the Finance Department Agent. You answer billing, invoice status, and financial compliance questions based solely on authorized finance evidence."),
            ("operations", "Operations Agent", "Supply chain tracking, inventory buffer, warehouse logistics, vendor SLAs", "You are the Operations Department Agent. You answer inventory availability, warehouse logistics, and supply chain questions based solely on authorized operations evidence.")
        ]

        for code, name, desc, prompt in agent_data:
            stmt = select(DepartmentAgent).where(DepartmentAgent.agent_code == code)
            if not (await session.execute(stmt)).scalar_one_or_none():
                session.add(DepartmentAgent(
                    department_id=dept_map[code].id,
                    agent_code=code,
                    name=name,
                    description=desc,
                    system_prompt=prompt,
                    is_enabled=True,
                    error_count=0
                ))
                print(f"Created Department Agent: {name}")

        # 8. Sample Knowledge Documents & Chunks across all 4 departments
        embedder = get_embedding_service()
        docs_data = [
            # Sales
            ("Q4 Enterprise Discounting & Pricing Authority Matrix", "sales_discounting_policy.txt", "sales", "internal",
             "Sales Representatives are authorized to offer up to a 10% standard discount. Any contract discount between 10% and 25% mandates Finance review and approval before contract sign-off."),
            ("Deal Qualification Framework (BANT/MEDDPIC)", "bant_qualification.txt", "sales", "internal",
             "Enterprise opportunities must demonstrate defined Budget, Economic Buyer, Decision Criteria, and Timeline before moving to stage Proposal."),
            ("Sales Partner Commission Guidelines 2026", "partner_commissions.txt", "sales", "internal",
             "Tier 1 enterprise partners receive 12% recurring revenue commission upon invoice payment clearance by Finance."),

            # HR
            ("Global Paid Time Off and Medical Leave Policy", "pto_medical_leave_2026.txt", "hr", "internal",
             "Standard annual leave allocation is 20 days per fiscal calendar. Sick leave permits up to 10 consecutive days with medical physician certification."),
            ("Performance Management and Promotion Review Cycles", "performance_cycles.txt", "hr", "internal",
             "Annual performance evaluations occur each November. Ratings include Unsatisfactory, Meets Expectations, and Exceeds Expectations."),
            ("Confidential Executive Compensation Policy", "executive_comp_restricted.txt", "hr", "confidential",
             "Restricted document. Executive equity grant vesting and base compensation schedules are strictly accessible to HR Management and Board."),

            # Finance
            ("Corporate Wire Payment Authority & Approval Protocol", "payment_authority_protocol.txt", "finance", "internal",
             "All outgoing vendor wire payments exceeding $5,000 mandate dual-authorization from the Finance Controller or Department Manager before disbursement."),
            ("Overdue Accounts Receivable Collection Procedures", "ar_collection_protocol.txt", "finance", "internal",
             "Invoices overdue past 30 days trigger automated credit hold alerts. Finance coordinates with Sales account owners to resolve disputed line items."),
            ("Enterprise Travel & Expense Reimbursement Policy", "expense_policy_2026.txt", "finance", "internal",
             "Per diem meal expense caps are established at $75/day. Hotel lodging receipts must accompany all expense report submissions within 14 days."),

            # Operations
            ("Warehouse Safety & Hazardous Materials Protocol", "ops_warehouse_safety.txt", "operations", "internal",
             "Warehouse employees must complete forklift certification before operating motorized equipment. High-density battery storage requires monitored thermal temperature control under 25 degrees Celsius."),
            ("Supply Chain Vendor Fulfillment SLA", "ops_supplier_sla.txt", "operations", "internal",
             "Tier-1 hardware suppliers must maintain 98.5% on-time fulfillment with maximum 48-hour shipment notice. Expedited freight is required for critical server hardware components."),
            ("Inventory Replenishment & Stock Buffer Policy", "ops_inventory_buffer.txt", "operations", "internal",
             "Critical optical networking and transceiver SKUs require a minimum 30-day buffer inventory on hand. Automated reorder notices are dispatched whenever stock falls below threshold levels.")
        ]

        for title, fname, dept_code, a_level, content in docs_data:
            stmt = select(Document).where(Document.filename == fname)
            if not (await session.execute(stmt)).scalar_one_or_none():
                doc = Document(
                    title=title,
                    filename=fname,
                    file_path=f"data/{fname}",
                    file_type="txt",
                    department_id=dept_map[dept_code].id,
                    access_level=a_level,
                    uploaded_by=user_map["admin@mesh.enterprise.internal"].id,
                    status="indexed"
                )
                session.add(doc)
                await session.flush()

                vec = embedder.embed_text(content)
                chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=0,
                    content=content,
                    page_number=1,
                    department_id=dept_map[dept_code].id,
                    access_level=a_level,
                    embedding=vec
                )
                session.add(chunk)

        # 9. Sensitive Action Requiring Human Approval (Pending Payment Example)
        stmt = select(ApprovalRequest).where(ApprovalRequest.idempotency_key == "demo-pending-wire-payment-001")
        if not (await session.execute(stmt)).scalar_one_or_none():
            expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
            session.add(ApprovalRequest(
                id="appr-demo-wire-payment-001",
                requester_id=user_map["finance.analyst@mesh.enterprise.internal"].id,
                requester_department_id=dept_map["finance"].id,
                action_type="payment_execution",
                target_resource="finance_invoice:INV-2026-002",
                requested_operation="execute_wire_transfer",
                payload={"invoice_number": "INV-2026-002", "amount": 180000.0, "vendor": "Titan Heavy Industries"},
                status="pending",
                idempotency_key="demo-pending-wire-payment-001",
                expires_at=expires
            ))

        # 10. Sample Pending Federation Access Request (Sales AE requesting Finance Invoice Clearance)
        stmt = select(FederationAccessRequest).where(FederationAccessRequest.idempotency_key == "demo-fed-sales-to-finance-001")
        if not (await session.execute(stmt)).scalar_one_or_none():
            expires_fed = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48)
            session.add(FederationAccessRequest(
                id="fed-req-demo-sales-fin-001",
                requester_user_id=user_map["sales.rep@mesh.enterprise.internal"].id,
                requester_department_id=dept_map["sales"].id,
                requesting_agent="sales_agent",
                source_department_id=dept_map["finance"].id,
                business_purpose="Verify payment clearance for Titan Heavy Industries deal",
                requested_fields=["invoice_number", "status", "due_date"],
                record_identifiers=["INV-2026-002"],
                access_duration_minutes=120,
                status="PENDING",
                idempotency_key="demo-fed-sales-to-finance-001",
                expires_at=expires_fed
            ))

        await session.commit()
        print("Idempotent synthetic data seeding completed successfully across all 4 departments!")


if __name__ == "__main__":
    asyncio.run(seed_all())
