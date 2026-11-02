import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
KB_DIR = BASE_DIR / "data" / "knowledge_base"

DEPARTMENTS = ["sales", "hr", "finance", "operations"]
for d in DEPARTMENTS:
    (KB_DIR / d).mkdir(parents=True, exist_ok=True)

# Document definitions: (filename, doc_id, title, access_level, topics, content_sections)
SALES_DOCS = [
    (
        "sales_pipeline_handbook.txt", "DOC-SALES-001", "Enterprise Sales Pipeline Handbook", "internal",
        ["pipeline", "stages", "deals", "crm"],
        """# Enterprise Sales Pipeline Handbook
Document ID: DOC-SALES-001
Department: Sales
Version: 2.1 (Synthetic Enterprise Policy Demo)
Access Level: internal
Effective Date: 2025-01-01 | Review Date: 2026-12-31

## 1. Overview and Lifecycle Stages
The Enterprise Sales Pipeline governs client acquisition across 5 standardized stages:
1. Lead: Initial contact identified, company verified, preliminary pain points logged.
2. Qualified: BANT criteria validated, decision maker identified, budget envelope confirmed.
3. Proposal: Solution architecture scoped, commercial terms drafted, executive summary delivered.
4. Closed Won: Contract counter-signed, initial invoice generated, customer success handoff scheduled.
5. Closed Lost: Prospect declined or delayed, competitor analysis logged, post-mortem review completed.

## 2. Velocity and Pipeline Health
Sales representatives must advance or close deals within 90 days. Deals lingering in Proposal stage exceeding 45 days automatically trigger a pipeline review with the Sales Manager."""
    ),
    (
        "lead_qualification_and_bant.txt", "DOC-SALES-002", "Lead Qualification and BANT Framework", "internal",
        ["bant", "qualification", "leads", "budget"],
        """# Lead Qualification and BANT Framework
Document ID: DOC-SALES-002
Department: Sales
Version: 1.8 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. The BANT Criteria
All enterprise opportunities exceeding $50,000 must satisfy strict BANT qualification:
- Budget: Prospect must possess allocated capital or verified line of business authority.
- Authority: The primary stakeholder must possess VP or C-level signing power.
- Need: Specific technological or operational pain point verifiable against our capabilities.
- Timeline: Target implementation date within 3 to 12 months.

## 2. Disqualification Criteria
Leads with indefinite budget cycles (>18 months) or unresolved regulatory blocks must be moved to 'nurture' status rather than remaining in active pipeline."""
    ),
    (
        "discount_approval_policy.txt", "DOC-SALES-003", "Commercial Discount Approval Matrix", "internal",
        ["discounts", "approvals", "pricing", "margins"],
        """# Commercial Discount Approval Matrix
Document ID: DOC-SALES-003
Department: Sales
Version: 3.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Discount Thresholds
- 0% to 5% Discount: Authorized autonomously by Sales Representative.
- 5.1% to 15% Discount: Requires written authorization from Sales Department Head.
- 15.1% to 25% Discount: Requires dual authorization from Sales Head and Finance Controller.
- Above 25% Discount: Strictly prohibited without Executive Committee sign-off.

## 2. Mandatory Pre-Conditions
No discount exceeding 10% may be offered unless client commits to minimum 24-month contract term and annual upfront billing."""
    ),
    (
        "proposal_management.txt", "DOC-SALES-004", "Enterprise Proposal Management Standard", "internal",
        ["proposals", "bids", "contracts", "rfp"],
        """# Enterprise Proposal Management Standard
Document ID: DOC-SALES-004
Department: Sales
Version: 1.5 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Proposal Requirements
Formal written proposals must include:
- Executive Summary outlining business problem and ROI projection.
- Scope of Work (SOW) with clear milestone deliverables.
- SLA commitments and support tier specification.
- Payment terms: Standard Net 30 days upon invoice delivery.

## 2. Legal Review Gateway
Any proposal with custom liability caps or modified indemnification clauses must be submitted to Legal counsel 5 business days prior to client delivery."""
    ),
    (
        "customer_onboarding.txt", "DOC-SALES-005", "Customer Onboarding and Handover Workflow", "internal",
        ["onboarding", "handover", "customer success"],
        """# Customer Onboarding and Handover Workflow
Document ID: DOC-SALES-005
Department: Sales
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Post-Signature Handoff
Within 48 hours of contract execution ('Closed Won'):
1. Account Executive creates transition ticket in CRM.
2. Introduction call scheduled between Customer and Customer Success Lead.
3. Access credentials provisioned through secure enterprise identity provider.
4. Operations notified if physical hardware delivery is mandated."""
    ),
    (
        "sales_forecasting.txt", "DOC-SALES-006", "Sales Forecasting and Quota Methodology", "internal",
        ["forecasting", "quotas", "revenue", "targets"],
        """# Sales Forecasting and Quota Methodology
Document ID: DOC-SALES-006
Department: Sales
Version: 2.2 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Weighted Pipeline Valuation
Forecasted quarterly revenue is computed based on stage probability weights:
- Lead: 10% weight.
- Qualified: 25% weight.
- Proposal: 50% weight.
- Contract Negotiation: 80% weight.
- Closed Won: 100% recognized revenue.

## 2. Weekly Reporting
All Account Executives must reconcile opportunity stages in CRM by Friday 17:00 local time."""
    ),
    (
        "contract_review.txt", "DOC-SALES-007", "Contract Review and Signature Delegation", "internal",
        ["contracts", "signatures", "delegation", "authority"],
        """# Contract Review and Signature Delegation
Document ID: DOC-SALES-007
Department: Sales
Version: 1.4 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Signature Authority
- Deals up to $100,000: Sales Department Manager.
- Deals $100,001 to $500,000: Sales Director and Corporate Controller.
- Deals above $500,000: Chief Executive Officer or Chief Financial Officer.
Sales Representatives cannot execute binding client contracts."""
    ),
    (
        "crm_data_definitions.txt", "DOC-SALES-008", "CRM Data Definitions and Dictionary", "internal",
        ["crm", "definitions", "fields", "data hygiene"],
        """# CRM Data Definitions and Dictionary
Document ID: DOC-SALES-008
Department: Sales
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Standard Fields
- Deal Value: Total contract value across primary term excluding optional renewals.
- Close Date: Target signature date agreed upon with client.
- Owner ID: Assigned internal Account Executive responsible for opportunity updates.
- Lead Source: Origin channel (Website, Outbound, Partner, Event)."""
    ),
    (
        "opportunity_probability_guidelines.txt", "DOC-SALES-009", "Opportunity Probability Guidelines", "internal",
        ["probability", "scoring", "guidelines"],
        """# Opportunity Probability Guidelines
Document ID: DOC-SALES-009
Department: Sales
Version: 1.2 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Objective Probability Assessment
Sales representatives must not manually inflate probability scores. Probability must reflect verifiable customer actions, such as budget sign-off or procurement vendor setup."""
    ),
    (
        "sales_reporting.txt", "DOC-SALES-010", "Sales Reporting and Dashboard Standards", "internal",
        ["reporting", "dashboards", "kpis", "metrics"],
        """# Sales Reporting and Dashboard Standards
Document ID: DOC-SALES-010
Department: Sales
Version: 1.1 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Core KPIs
- Win Rate: Closed won opportunities divided by total completed opportunities.
- Average Sales Cycle: Elapsed days from lead creation to contract signature.
- Average Deal Size: Total closed ARR divided by closed deal volume."""
    ),
    (
        "escalation_procedures.txt", "DOC-SALES-011", "Client Escalation and Deal Salvage Procedures", "internal",
        ["escalation", "retention", "customer disputes"],
        """# Client Escalation and Deal Salvage Procedures
Document ID: DOC-SALES-011
Department: Sales
Version: 1.3 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Trigger Conditions
If a tier-1 customer expresses dissatisfaction with contract terms or threatens cancellation:
1. Account Executive must log an escalation incident within 2 hours.
2. Sales Manager joins client sync within 24 hours.
3. Product or Operations leads looped in if delivery issues are the root cause."""
    ),
    (
        "sales_faq.txt", "DOC-SALES-012", "Sales Department Frequently Asked Questions", "internal",
        ["faq", "questions", "guidance"],
        """# Sales Department Frequently Asked Questions
Document ID: DOC-SALES-012
Department: Sales
Version: 3.1 (Synthetic Enterprise Policy Demo)
Access Level: internal

## FAQ 1: Can I query finance invoice statuses for my clients?
Yes, using the Sales AI Agent, cross-department requests to Finance for invoice status checks are authorized under the Federation Gateway policy agreement.

## FAQ 2: What is the maximum discount I can offer without manager approval?
Up to 5%. Any discount exceeding 5% requires Sales Head approval, and exceeding 15% requires Finance sign-off."""
    )
]

HR_DOCS = [
    (
        "leave_and_attendance_policy.txt", "DOC-HR-001", "Comprehensive Leave and Attendance Policy", "internal",
        ["leave", "pto", "vacation", "sick leave", "attendance"],
        """# Comprehensive Leave and Attendance Policy
Document ID: DOC-HR-001
Department: Human Resources
Version: 2.5 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Annual Paid Time Off (PTO)
Full-time employees accrue 20 days of paid vacation per calendar year. Up to 5 unused PTO days can be rolled over into the subsequent calendar year.

## 2. Sick and Medical Leave
Employees receive 10 days of paid sick leave annually. Medical absences exceeding 3 consecutive business days require a physician's note submitted to HR."""
    ),
    (
        "recruitment_process.txt", "DOC-HR-002", "Talent Acquisition and Hiring Procedures", "internal",
        ["recruitment", "hiring", "interviews", "offers"],
        """# Talent Acquisition and Hiring Procedures
Document ID: DOC-HR-002
Department: Human Resources
Version: 1.7 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Hiring Stages
1. Job Requisition Approval: Authorized by Department Head and Finance.
2. Sourcing and Screening: Initial HR phone interview.
3. Technical/Functional Evaluation: Two panel interviews with hiring team.
4. Executive and Culture Interview: Final alignment meeting.
5. Offer Formulation: Standardized compensation benchmarks applied."""
    ),
    (
        "employee_onboarding.txt", "DOC-HR-003", "New Hire Onboarding Roadmap", "internal",
        ["onboarding", "new hires", "training", "setup"],
        """# New Hire Onboarding Roadmap
Document ID: DOC-HR-003
Department: Human Resources
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Day 1 Deliverables
- Completion of employment contract and tax withholding verification.
- IT asset allocation and workstation security posture validation.
- Review of enterprise Code of Conduct and Zero-Trust Data Security protocols."""
    ),
    (
        "benefits_policy.txt", "DOC-HR-004", "Employee Health and Welfare Benefits Handbook", "internal",
        ["benefits", "insurance", "healthcare", "401k", "pension"],
        """# Employee Health and Welfare Benefits Handbook
Document ID: DOC-HR-004
Department: Human Resources
Version: 3.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Medical and Dental Coverage
Comprehensive health, dental, and vision insurance is provided to all full-time staff with 80% employer premium contribution.

## 2. Retirement Matching
The company matches employee 401(k) retirement contributions up to 5% of base salary."""
    ),
    (
        "code_of_conduct.txt", "DOC-HR-005", "Enterprise Code of Ethical Conduct", "internal",
        ["ethics", "conduct", "compliance", "integrity"],
        """# Enterprise Code of Ethical Conduct
Document ID: DOC-HR-005
Department: Human Resources
Version: 4.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Professional Integrity
Employees must maintain honesty, mutual respect, and zero tolerance for harassment, discrimination, or conflict of interest in all corporate activities."""
    ),
    (
        "performance_reviews.txt", "DOC-HR-006", "Annual Performance Appraisal Framework", "internal",
        ["performance", "appraisal", "kpis", "reviews"],
        """# Annual Performance Appraisal Framework
Document ID: DOC-HR-006
Department: Human Resources
Version: 2.1 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Review Cycle
Evaluations take place annually in November:
- Self-Evaluation (20% weight)
- Manager Review (50% weight)
- Peer 360 Feedback (30% weight)"""
    ),
    (
        "training_and_development.txt", "DOC-HR-007", "Professional Training and Development Stipend", "internal",
        ["training", "education", "stipend", "development"],
        """# Professional Training and Development Stipend
Document ID: DOC-HR-007
Department: Human Resources
Version: 1.6 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Annual Learning Allowance
Full-time employees with at least 6 months tenure are entitled to an annual $2,500 training stipend for approved certifications, conferences, and coursework."""
    ),
    (
        "grievance_procedures.txt", "DOC-HR-008", "Formal Employee Grievance Procedure", "internal",
        ["grievance", "disputes", "confidentiality"],
        """# Formal Employee Grievance Procedure
Document ID: DOC-HR-008
Department: Human Resources
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Filing Process
Employees may submit formal grievances directly to HR Management or via the anonymous internal ethics hotline. Retaliation against any reporting employee is strictly illegal and grounds for immediate termination."""
    ),
    (
        "workplace_safety.txt", "DOC-HR-009", "Workplace Safety and Ergonomics Protocol", "internal",
        ["safety", "ergonomics", "health", "hazard"],
        """# Workplace Safety and Ergonomics Protocol
Document ID: DOC-HR-009
Department: Human Resources
Version: 1.3 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Ergonomic Standards
The company provides ergonomic assessments and adjustable workstations to prevent repetitive strain injuries."""
    ),
    (
        "hr_data_access_policy.txt", "DOC-HR-010", "HR Data Privacy and Compensation Masking Policy", "confidential",
        ["privacy", "salary", "compensation", "access control"],
        """# HR Data Privacy and Compensation Masking Policy
Document ID: DOC-HR-010
Department: Human Resources
Version: 3.2 (Synthetic Enterprise Policy Demo)
Access Level: confidential

## 1. Salary and Compensation Masking
Compensation, bonuses, and equity grants are strictly classified. Non-managerial staff cannot view compensation data of any colleague. Only the HR Director and Corporate Controller possess unmasked salary access."""
    ),
    (
        "confidentiality_procedures.txt", "DOC-HR-011", "Personnel File Confidentiality Procedures", "confidential",
        ["confidentiality", "personnel files", "gdpr"],
        """# Personnel File Confidentiality Procedures
Document ID: DOC-HR-011
Department: Human Resources
Version: 2.1 (Synthetic Enterprise Policy Demo)
Access Level: confidential

## 1. Record Retention
Employee medical notes, disciplinary letters, and background checks are retained in encrypted storage for 7 years post-departure."""
    ),
    (
        "hr_faq.txt", "DOC-HR-012", "Human Resources Frequently Asked Questions", "internal",
        ["faq", "pto", "benefits", "leave balance"],
        """# Human Resources Frequently Asked Questions
Document ID: DOC-HR-012
Department: Human Resources
Version: 3.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## FAQ 1: How do I check my remaining vacation balance?
You can ask the HR AI Agent: "What is my current leave balance?"

## FAQ 2: Can other employees see my salary?
No. All compensation attributes are filtered server-side by the Zero-Trust RBAC layer."""
    )
]

FINANCE_DOCS = [
    (
        "invoice_processing.txt", "DOC-FIN-001", "Standard Invoice Processing Guideline", "internal",
        ["invoices", "billing", "accounts payable", "net30"],
        """# Standard Invoice Processing Guideline
Document ID: DOC-FIN-001
Department: Finance
Version: 2.3 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Invoice Ingestion and Verification
Invoices submitted by vendors must match an approved Purchase Order (PO). Invoices without a valid PO reference will be rejected automatically."""
    ),
    (
        "accounts_payable.txt", "DOC-FIN-002", "Accounts Payable Settlement Protocol", "internal",
        ["payable", "payments", "vendors", "settlement"],
        """# Accounts Payable Settlement Protocol
Document ID: DOC-FIN-002
Department: Finance
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Payment Terms
Standard vendor disbursements occur on Net 30 terms. Early settlement discounts (2% Net 10) must be evaluated and captured where cash flow permits."""
    ),
    (
        "accounts_receivable.txt", "DOC-FIN-003", "Accounts Receivable and Dunning Policy", "internal",
        ["receivable", "overdue", "collections", "dunning"],
        """# Accounts Receivable and Dunning Policy
Document ID: DOC-FIN-003
Department: Finance
Version: 2.2 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Overdue Classification
- 1 to 15 Days Overdue: Automated reminder email sent to client billing contact.
- 16 to 30 Days Overdue: Account Executive alerted to perform direct outreach.
- Over 30 Days Overdue: Customer account placed on credit hold."""
    ),
    (
        "expense_reimbursement.txt", "DOC-FIN-004", "Employee Business Expense Reimbursement", "internal",
        ["expenses", "travel", "meals", "reimbursement"],
        """# Employee Business Expense Reimbursement
Document ID: DOC-FIN-004
Department: Finance
Version: 3.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Allowable Daily Limits
- Travel Meals: Up to $85 per diem.
- Domestic Lodging: Up to $250 per night (metropolitan areas adjusted to $350).
- Receipts mandatory for all items exceeding $25."""
    ),
    (
        "budget_approval.txt", "DOC-FIN-005", "Departmental Budget Allocation and Approval", "internal",
        ["budget", "fiscal", "allocation", "spending"],
        """# Departmental Budget Allocation and Approval
Document ID: DOC-FIN-005
Department: Finance
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Annual Budget Preparation
Departmental managers must submit annual operating expenditure proposals by October 15 for Finance review."""
    ),
    (
        "vendor_onboarding.txt", "DOC-FIN-006", "Vendor Financial Verification and Setup", "internal",
        ["vendors", "w9", "banking", "compliance"],
        """# Vendor Financial Verification and Setup
Document ID: DOC-FIN-006
Department: Finance
Version: 1.8 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Mandatory Compliance Checks
All new vendors must supply a verified W-9 / W-8BEN, certificate of insurance, and bank account validation letter before receiving disbursements."""
    ),
    (
        "payment_approval_thresholds.txt", "DOC-FIN-007", "Payment Authorization and Dual Control Thresholds", "confidential",
        ["thresholds", "wire", "approval", "dual control"],
        """# Payment Authorization and Dual Control Thresholds
Document ID: DOC-FIN-007
Department: Finance
Version: 4.1 (Synthetic Enterprise Policy Demo)
Access Level: confidential

## 1. Authorization Levels
- Up to $10,000: Single authorization by Department Manager.
- $10,001 to $50,000: Controller authorization required.
- Over $50,000: Mandatory Dual Authorization by Controller and CFO."""
    ),
    (
        "wire_transfer_controls.txt", "DOC-FIN-008", "Wire Transfer and Electronic Funds Security", "confidential",
        ["wire transfer", "security", "anti-fraud", "banking"],
        """# Wire Transfer and Electronic Funds Security
Document ID: DOC-FIN-008
Department: Finance
Version: 3.5 (Synthetic Enterprise Policy Demo)
Access Level: confidential

## 1. Anti-Fraud Out-of-Band Verification
Any change to vendor bank account or remittance coordinates requires an out-of-band telephone verification before funds release. AI agents are strictly prohibited from executing wire transfers autonomously."""
    ),
    (
        "financial_data_access.txt", "DOC-FIN-009", "Financial Record Classification and Access Policy", "confidential",
        ["classification", "confidentiality", "ledger"],
        """# Financial Record Classification and Access Policy
Document ID: DOC-FIN-009
Department: Finance
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: confidential

## 1. Perimeter Restrictions
General ledger, profit margin calculations, and tax filings are restricted strictly to Finance personnel."""
    ),
    (
        "reconciliation_procedures.txt", "DOC-FIN-010", "Monthly Bank and Ledger Reconciliation", "internal",
        ["reconciliation", "closing", "ledger", "month-end"],
        """# Monthly Bank and Ledger Reconciliation
Document ID: DOC-FIN-010
Department: Finance
Version: 1.9 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Month-End Close Timeline
All bank accounts, corporate credit cards, and ledger clearing accounts must be fully reconciled by Day 5 of the subsequent calendar month."""
    ),
    (
        "fraud_escalation.txt", "DOC-FIN-011", "Financial Irregularity and Fraud Escalation Procedure", "confidential",
        ["fraud", "whistleblower", "investigation"],
        """# Financial Irregularity and Fraud Escalation Procedure
Document ID: DOC-FIN-011
Department: Finance
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: confidential

## 1. Immediate Suspension
Upon detection of suspected invoice tampering or unauthorized disbursements, the associated vendor account is frozen immediately and the Audit Committee notified."""
    ),
    (
        "finance_faq.txt", "DOC-FIN-012", "Finance Department Frequently Asked Questions", "internal",
        ["faq", "invoices", "payments", "status"],
        """# Finance Department Frequently Asked Questions
Document ID: DOC-FIN-012
Department: Finance
Version: 3.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## FAQ 1: Can the Finance AI Agent execute a wire payment directly?
No. Financial disbursements are sensitive actions that pause execution and create a Human Approval Request requiring authorized manager sign-off."""
    )
]

OPERATIONS_DOCS = [
    (
        "inventory_management.txt", "DOC-OPS-001", "Warehouse Inventory Management Standard", "internal",
        ["inventory", "warehouse", "stock", "skus"],
        """# Warehouse Inventory Management Standard
Document ID: DOC-OPS-001
Department: Operations
Version: 2.2 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Inventory Organization and SKUs
All physical items in enterprise warehouses must bear a scannable barcode matching their unique SKU. Stock is segmented across Zone A (Fast-moving), Zone B (Standard), and Zone C (Bulk)."""
    ),
    (
        "reorder_procedures.txt", "DOC-OPS-002", "Automated Stock Reorder and Safety Levels", "internal",
        ["reorder", "safety stock", "replenishment", "procurement"],
        """# Automated Stock Reorder and Safety Levels
Document ID: DOC-OPS-002
Department: Operations
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Minimum Threshold Rules
When quantity on hand drops below the defined reorder threshold, an automated purchase order recommendation is triggered to the primary supplier."""
    ),
    (
        "warehouse_receiving.txt", "DOC-OPS-003", "Warehouse Inbound Receiving and Inspection", "internal",
        ["receiving", "inspection", "dock", "inbound"],
        """# Warehouse Inbound Receiving and Inspection
Document ID: DOC-OPS-003
Department: Operations
Version: 1.8 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Delivery Check-In
Shipments arriving at warehouse docks must be verified against vendor packing slips within 4 hours. Damaged containers must be documented photographically."""
    ),
    (
        "stock_adjustment_policy.txt", "DOC-OPS-004", "Physical Stock Discrepancy Adjustment", "internal",
        ["discrepancy", "shrinkage", "audit", "adjustment"],
        """# Physical Stock Discrepancy Adjustment
Document ID: DOC-OPS-004
Department: Operations
Version: 1.5 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Variance Investigation
Any physical count variance exceeding 5 units or $1,000 value requires formal supervisor sign-off and an incident log."""
    ),
    (
        "supplier_management.txt", "DOC-OPS-005", "Supplier Quality and Performance SLA", "internal",
        ["suppliers", "sla", "lead time", "quality"],
        """# Supplier Quality and Performance SLA
Document ID: DOC-OPS-005
Department: Operations
Version: 2.1 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Scorecard Metrics
Suppliers must maintain 98% on-time delivery rate and $<1\%$ defect rate over each rolling 6-month period."""
    ),
    (
        "fulfillment_workflows.txt", "DOC-OPS-006", "Order Fulfillment and Dispatch Protocol", "internal",
        ["fulfillment", "shipping", "dispatch", "logistics"],
        """# Order Fulfillment and Dispatch Protocol
Document ID: DOC-OPS-006
Department: Operations
Version: 2.3 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Pick, Pack, and Ship Timeline
Customer orders approved prior to 14:00 local time must be dispatched the same business day."""
    ),
    (
        "equipment_maintenance.txt", "DOC-OPS-007", "Facility Equipment and Preventive Maintenance", "internal",
        ["maintenance", "machinery", "safety", "forklifts"],
        """# Facility Equipment and Preventive Maintenance
Document ID: DOC-OPS-007
Department: Operations
Version: 1.4 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Scheduled Servicing
Forklifts, conveyor belts, and packing machines undergo quarterly mechanical inspections and electrical safety certification."""
    ),
    (
        "incident_escalation.txt", "DOC-OPS-008", "Supply Chain Disruption Escalation Protocol", "internal",
        ["incident", "disruption", "delay", "escalation"],
        """# Supply Chain Disruption Escalation Protocol
Document ID: DOC-OPS-008
Department: Operations
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Carrier Delays
If shipping transit is delayed by more than 48 hours, carrier alerts are escalated to Logistics Coordinator and Sales team."""
    ),
    (
        "warehouse_safety.txt", "DOC-OPS-009", "Warehouse Occupational Safety and PPE Standard", "internal",
        ["safety", "ppe", "osha", "hazards"],
        """# Warehouse Occupational Safety and PPE Standard
Document ID: DOC-OPS-009
Department: Operations
Version: 3.1 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Mandatory PPE
High-visibility vests, steel-toed boots, and hard hats are mandatory across all warehouse staging zones."""
    ),
    (
        "purchase_orders.txt", "DOC-OPS-010", "Purchase Order Issuance and Fulfillment Tracking", "internal",
        ["purchase orders", "po", "procurement", "fulfillment"],
        """# Purchase Order Issuance and Fulfillment Tracking
Document ID: DOC-OPS-010
Department: Operations
Version: 2.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. PO Numbering
All purchase orders follow standard nomenclature `PO-YYYY-XXXXX` and bind the supplier to fixed commercial pricing."""
    ),
    (
        "logistics_reporting.txt", "DOC-OPS-011", "Logistics Metrics and Fleet Reporting", "internal",
        ["logistics", "freight", "turnover", "reporting"],
        """# Logistics Metrics and Fleet Reporting
Document ID: DOC-OPS-011
Department: Operations
Version: 1.3 (Synthetic Enterprise Policy Demo)
Access Level: internal

## 1. Operational KPIs
- Inventory Turnover Ratio
- On-Time In-Full (OTIF) Delivery Percentage
- Order Lead Time in Hours"""
    ),
    (
        "operations_faq.txt", "DOC-OPS-012", "Operations Department Frequently Asked Questions", "internal",
        ["faq", "sku", "inventory", "stock status"],
        """# Operations Department Frequently Asked Questions
Document ID: DOC-OPS-012
Department: Operations
Version: 3.0 (Synthetic Enterprise Policy Demo)
Access Level: internal

## FAQ 1: Can Sales query our inventory stock levels?
Yes. The Federation Gateway allows the Sales Agent to query item SKUs, descriptions, quantity on hand, and stock status."""
    )
]


def generate_all_documents():
    dept_configs = [
        ("sales", SALES_DOCS),
        ("hr", HR_DOCS),
        ("finance", FINANCE_DOCS),
        ("operations", OPERATIONS_DOCS)
    ]

    total_created = 0
    for dept, docs in dept_configs:
        for filename, doc_id, title, access, topics, content in docs:
            file_path = KB_DIR / dept / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            total_created += 1

    print(f"Successfully generated {total_created} knowledge documents across 4 departments in {KB_DIR}.")


if __name__ == "__main__":
    generate_all_documents()
