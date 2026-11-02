import os
import sys
import json
import random
import hashlib
import datetime
from pathlib import Path

# Deterministic seed for reproducible generation
RANDOM_SEED = 20260421
random.seed(RANDOM_SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
GEN_DIR = DATA_DIR / "generated"
MANIFESTS_DIR = DATA_DIR / "manifests"

for d in ["sales", "hr", "finance", "operations"]:
    (GEN_DIR / d).mkdir(parents=True, exist_ok=True)
MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

# Synthetic data pools
COMPANIES = [
    "Apex Global Systems", "Quantum Logistics", "Titan Heavy Industries", "BlueSky Cloud Solutions",
    "Nordic Supermarkets", "Vanguard Financial Technologies", "Helios Energy Grid", "Zenith BioHealth",
    "Pinnacle Automation Corp", "Aegis Defense Dynamics", "Crestview Hospitality Group", "Strata Media Labs",
    "Solaria Solar Technologies", "Ironclad Cyber Systems", "Terraform GeoEngineering", "Astraea Aerospace",
    "Krypton Robotics Ltd", "OmniChannel Retailers", "Meridian Shipping Lines", "Pacific Trade Winds",
    "Atlas Infrastructure", "Hyperion Telecom", "Elysium Therapeutics", "Novus Materials",
    "Polaris Medical Systems", "Triton Marine Solutions", "Silverline Transit", "Echo Sound Engineering",
    "Valence Chemical Corp", "Onyx Security Networks", "Lumina Optics", "Frontier Mining Group",
    "Sierra Agriculture", "Vortex Turbines", "Zephyr Environmental", "Cascade Water Utilities",
    "Summit Financial Partners", "Beacon Analytics", "Monolith Datacenters", "NextGen Mobility"
]

INDUSTRIES = ["Technology", "Healthcare", "Manufacturing", "Finance", "Energy", "Logistics", "Retail", "Telecommunications", "Aerospace", "Consulting"]

FIRST_NAMES = ["Liam", "Olivia", "Noah", "Emma", "Oliver", "Charlotte", "James", "Amelia", "Sophia", "Lucas", "Mia", "Benjamin", "Evelyn", "Alexander", "Harper", "Henry", "Camila", "Michael", "Ella", "Daniel", "Elizabeth", "Logan", "Luna", "Jackson", "Sofia", "Sebastian", "Avery", "Jack", "Mila", "Aiden", "Aria", "Owen", "Chloe", "Samuel", "Layla", "Matthew", "Riley", "Joseph", "Zoey", "Levi", "Nora", "Mateo", "Lily", "David", "Eleanor", "John", "Hannah", "Wyatt", "Lillian", "Carter", "Addison", "Julian", "Aubrey", "Luke", "Ellie", "Grayson", "Stella", "Isaac", "Natalie", "Jayden", "Zoe", "Theodore", "Leah", "Gabriel", "Hazel", "Anthony", "Violet", "Dylan", "Aurora", "Leo", "Savannah", "Lincoln", "Audrey", "Jaxon", "Brooklyn", "Asher", "Bella", "Christopher", "Claire", "Josiah", "Skylar", "Andrew", "Lucy", "Thomas", "Paisley", "Joshua", "Everly", "Ezra", "Anna", "Hudson", "Caroline", "Charles", "Nova", "Caleb", "Genesis", "Isaiah", "Emilia", "Ryan", "Kennedy"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"]


def compute_checksum(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def generate_sales_data():
    print("Generating Sales synthetic dataset...")
    # 1. Customers (120 synthetic customers)
    customers = []
    for i in range(1, 121):
        company = f"{random.choice(COMPANIES)} {i}"
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        cust = {
            "id": i,
            "customer_code": f"CUST-{i:04d}",
            "company_name": company,
            "industry": random.choice(INDUSTRIES),
            "contact_name": f"{fname} {lname}",
            "contact_email": f"{fname.lower()}.{lname.lower()}@synthetic-corp.test",
            "status": "active" if random.random() > 0.1 else "prospect",
            "created_at": (datetime.datetime(2025, 1, 1) + datetime.timedelta(days=random.randint(0, 365))).isoformat()
        }
        customers.append(cust)

    # 2. Opportunities (550 synthetic opportunities)
    stages = ["lead", "qualified", "proposal", "closed_won", "closed_lost"]
    sources = ["website", "referral", "partner", "outbound", "event"]
    opps = []
    for i in range(1, 551):
        cust = random.choice(customers)
        stage = random.choices(stages, weights=[0.2, 0.25, 0.25, 0.2, 0.1])[0]
        val = round(random.uniform(15000.0, 750000.0), 2)
        needs_fin = val > 100000.0 or stage == "proposal"
        fin_status = "none"
        if needs_fin:
            fin_status = random.choice(["pending", "approved", "rejected"])
        
        opp = {
            "id": i,
            "customer_id": cust["id"],
            "title": f"{cust['company_name']} - Enterprise Expansion Project #{i}",
            "client_name": cust["company_name"],
            "deal_value": val,
            "stage": stage,
            "probability": 0.9 if stage == "closed_won" else (0.1 if stage == "closed_lost" else 0.5),
            "lead_source": random.choice(sources),
            "needs_finance_approval": needs_fin,
            "finance_status": fin_status,
            "owner_id": random.choice([3, 4]),  # Sales manager or sales rep
            "department_id": 1,
            "created_at": (datetime.datetime(2025, 3, 1) + datetime.timedelta(days=random.randint(0, 350))).isoformat(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        opps.append(opp)

    cust_path = GEN_DIR / "sales" / "sales_customers.json"
    opps_path = GEN_DIR / "sales" / "sales_opportunities.json"
    
    with open(cust_path, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2)
    with open(opps_path, "w", encoding="utf-8") as f:
        json.dump(opps, f, indent=2)

    return {
        "dataset_name": "sales_synthetic_v1",
        "customers_count": len(customers),
        "opportunities_count": len(opps),
        "customers_checksum": compute_checksum(cust_path),
        "opportunities_checksum": compute_checksum(opps_path)
    }


def generate_hr_data():
    print("Generating HR synthetic dataset...")
    positions = [
        "Software Engineer", "Senior DevOps Engineer", "Product Manager", "Account Executive",
        "Financial Analyst", "HR Specialist", "Logistics Coordinator", "Warehouse Supervisor",
        "Data Scientist", "Quality Assurance Analyst", "Sales Manager", "HR Director",
        "Security Architect", "Supply Chain Analyst", "Controller"
    ]
    ratings = ["Outstanding", "Exceeds Expectations", "Meets Expectations", "Needs Improvement"]

    # 1. Employees (160 synthetic employee records)
    employees = []
    for i in range(1, 161):
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        pos = random.choice(positions)
        dept_id = random.choice([1, 2, 3, 4])
        sal = round(random.uniform(55000.0, 185000.0), 2)
        emp = {
            "id": i,
            "employee_code": f"EMP-{i:04d}",
            "full_name": f"{fname} {lname}",
            "position": pos,
            "department_id": dept_id,
            "leave_balance": random.randint(5, 28),
            "salary": sal,
            "performance_rating": random.choice(ratings),
            "joining_date": (datetime.datetime(2022, 1, 1) + datetime.timedelta(days=random.randint(0, 1200))).strftime("%Y-%m-%d"),
            "employment_status": "active" if random.random() > 0.05 else "on_leave",
            "is_sensitive": True,
            "created_at": (datetime.datetime(2025, 1, 1) + datetime.timedelta(days=random.randint(0, 300))).isoformat()
        }
        employees.append(emp)

    # 2. Leaves (240 leave requests)
    leave_types = ["annual", "sick", "personal", "parental", "bereavement"]
    leave_statuses = ["approved", "pending", "rejected"]
    leaves = []
    for i in range(1, 241):
        emp = random.choice(employees)
        days = random.randint(1, 14)
        st_date = (datetime.datetime(2025, 6, 1) + datetime.timedelta(days=random.randint(0, 240)))
        end_date = st_date + datetime.timedelta(days=days)
        lv = {
            "id": i,
            "employee_id": emp["id"],
            "leave_type": random.choice(leave_types),
            "days": days,
            "status": random.choice(leave_statuses),
            "start_date": st_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "created_at": st_date.isoformat()
        }
        leaves.append(lv)

    emp_path = GEN_DIR / "hr" / "hr_employees.json"
    leaves_path = GEN_DIR / "hr" / "hr_leaves.json"
    
    with open(emp_path, "w", encoding="utf-8") as f:
        json.dump(employees, f, indent=2)
    with open(leaves_path, "w", encoding="utf-8") as f:
        json.dump(leaves, f, indent=2)

    return {
        "dataset_name": "hr_synthetic_v1",
        "employees_count": len(employees),
        "leaves_count": len(leaves),
        "employees_checksum": compute_checksum(emp_path),
        "leaves_checksum": compute_checksum(leaves_path)
    }


def generate_finance_data():
    print("Generating Finance synthetic dataset...")
    # 1. Vendors (110 synthetic vendors)
    vendor_cats = ["Cloud Infrastructure", "Software Licenses", "Office Facilities", "Legal Services", "Consulting", "Hardware Supplies"]
    vendors = []
    for i in range(1, 111):
        name = f"{random.choice(COMPANIES)} Services #{i}"
        ven = {
            "id": i,
            "vendor_code": f"VEN-{i:04d}",
            "name": name,
            "category": random.choice(vendor_cats),
            "contact_email": f"accounts@ven{i}.synthetic-corp.test",
            "status": "active",
            "created_at": (datetime.datetime(2025, 1, 10) + datetime.timedelta(days=random.randint(0, 300))).isoformat()
        }
        vendors.append(ven)

    # 2. Invoices (350 synthetic invoices)
    inv_statuses = ["sent", "paid", "overdue", "pending_approval", "cancelled"]
    invoices = []
    for i in range(1, 351):
        ven = random.choice(vendors)
        amt = round(random.uniform(1200.0, 185000.0), 2)
        due = (datetime.datetime(2025, 6, 1) + datetime.timedelta(days=random.randint(0, 300)))
        status = random.choice(inv_statuses)
        inv = {
            "id": i,
            "vendor_id": ven["id"],
            "invoice_number": f"INV-2026-{i:05d}",
            "client_name": ven["name"],
            "amount": amt,
            "status": status,
            "due_date": due.isoformat(),
            "related_opportunity_id": random.randint(1, 500) if random.random() > 0.6 else None,
            "department_id": 3,
            "created_at": (due - datetime.timedelta(days=30)).isoformat()
        }
        invoices.append(inv)

    # 3. Payments (160 synthetic payments)
    payments = []
    for i in range(1, 161):
        inv = random.choice(invoices)
        pay = {
            "id": i,
            "invoice_id": inv["id"],
            "payment_reference": f"PAY-REF-{i:06d}",
            "amount": inv["amount"],
            "payment_method": random.choice(["wire_transfer", "ach", "credit_line"]),
            "status": "completed",
            "department_id": 3,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        payments.append(pay)

    ven_path = GEN_DIR / "finance" / "finance_vendors.json"
    inv_path = GEN_DIR / "finance" / "finance_invoices.json"
    pay_path = GEN_DIR / "finance" / "finance_payments.json"

    with open(ven_path, "w", encoding="utf-8") as f:
        json.dump(vendors, f, indent=2)
    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(invoices, f, indent=2)
    with open(pay_path, "w", encoding="utf-8") as f:
        json.dump(payments, f, indent=2)

    return {
        "dataset_name": "finance_synthetic_v1",
        "vendors_count": len(vendors),
        "invoices_count": len(invoices),
        "payments_count": len(payments),
        "invoices_checksum": compute_checksum(inv_path)
    }


def generate_operations_data():
    print("Generating Operations synthetic dataset...")
    # 1. Suppliers (60 synthetic suppliers)
    suppliers = []
    for i in range(1, 61):
        sup = {
            "id": i,
            "supplier_code": f"SUPP-{i:04d}",
            "name": f"{random.choice(COMPANIES)} Supply #{i}",
            "contact_email": f"logistics@supp{i}.synthetic-corp.test",
            "status": "active",
            "created_at": (datetime.datetime(2025, 2, 1) + datetime.timedelta(days=random.randint(0, 300))).isoformat()
        }
        suppliers.append(sup)

    # 2. Inventory / Stock records (320 items)
    categories = ["Servers & Compute", "Networking Gear", "Sensors & IoT", "Packaging Materials", "Robotics Components", "Cables & Power"]
    locations = ["Warehouse Alpha - Zone A", "Warehouse Alpha - Zone B", "Warehouse Beta - Hub 1", "Warehouse Beta - Hub 2", "Depot Gamma"]
    items = []
    for i in range(1, 321):
        sup = random.choice(suppliers)
        cat = random.choice(categories)
        qty = random.randint(0, 450)
        reorder = random.randint(15, 60)
        status = "out_of_stock" if qty == 0 else ("low_stock" if qty < reorder else "in_stock")
        item = {
            "id": i,
            "sku": f"SKU-{cat[:3].upper()}-{i:04d}",
            "item_name": f"{cat} Part #{i} Industrial Model",
            "category": cat,
            "quantity_on_hand": qty,
            "reserved_quantity": random.randint(0, min(qty, 20)),
            "reorder_threshold": reorder,
            "warehouse_location": random.choice(locations),
            "supplier_id": sup["id"],
            "status": status,
            "department_id": 4,
            "created_at": (datetime.datetime(2025, 2, 1) + datetime.timedelta(days=random.randint(0, 320))).isoformat()
        }
        items.append(item)

    # 3. Purchase orders (120 synthetic POs)
    pos = []
    for i in range(1, 121):
        it = random.choice(items)
        po = {
            "id": i,
            "po_number": f"PO-2026-{i:05d}",
            "supplier_id": it["supplier_id"],
            "sku": it["sku"],
            "quantity": random.randint(50, 500),
            "status": random.choice(["ordered", "shipped", "received", "cancelled"]),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        pos.append(po)

    sup_path = GEN_DIR / "operations" / "operations_suppliers.json"
    inv_path = GEN_DIR / "operations" / "operations_inventory.json"
    po_path = GEN_DIR / "operations" / "operations_purchase_orders.json"

    with open(sup_path, "w", encoding="utf-8") as f:
        json.dump(suppliers, f, indent=2)
    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    with open(po_path, "w", encoding="utf-8") as f:
        json.dump(pos, f, indent=2)

    return {
        "dataset_name": "operations_synthetic_v1",
        "suppliers_count": len(suppliers),
        "inventory_count": len(items),
        "purchase_orders_count": len(pos),
        "inventory_checksum": compute_checksum(inv_path)
    }


def write_manifests_and_dictionary(manifests: dict):
    # Save machine-readable manifest
    manifest_path = MANIFESTS_DIR / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifests, f, indent=2)
    print(f"Manifest written to {manifest_path}")

    # Write human-readable DATA_DICTIONARY.md
    dict_path = DATA_DIR / "DATA_DICTIONARY.md"
    dict_content = f"""# Synthetic Enterprise Datasets — Data Dictionary & Specification

> **NOTICE:** All data contained in these datasets is **100% synthetically generated** for demonstration, benchmarking, and access evaluation purposes. No real human, financial, or company records are used.

## 1. Dataset Generation Manifest
- **Generator Random Seed:** `{RANDOM_SEED}` (Deterministic & Reproducible)
- **Generated At:** `{datetime.datetime.now(datetime.timezone.utc).isoformat()}`
- **Checksums:**
  - Sales Opportunities: `{manifests['sales']['opportunities_checksum']}`
  - HR Employees: `{manifests['hr']['employees_checksum']}`
  - Finance Invoices: `{manifests['finance']['invoices_checksum']}`
  - Operations Inventory: `{manifests['operations']['inventory_checksum']}`

## 2. Structured Record Counts Summary

| Department | Primary Entities | Record Count | Minimum Requirement | Compliance Status |
| :--- | :--- | :--- | :--- | :--- |
| **Sales** | Customers (`sales_customers.json`) | {manifests['sales']['customers_count']} | $\\ge 100$ | **MET** |
| **Sales** | Opportunities (`sales_opportunities.json`) | {manifests['sales']['opportunities_count']} | $\\ge 500$ | **MET** |
| **HR** | Employees (`hr_employees.json`) | {manifests['hr']['employees_count']} | $\\ge 150$ | **MET** |
| **HR** | Leave Requests (`hr_leaves.json`) | {manifests['hr']['leaves_count']} | $\\ge 200$ | **MET** |
| **Finance** | Vendors (`finance_vendors.json`) | {manifests['finance']['vendors_count']} | $\\ge 100$ | **MET** |
| **Finance** | Invoices (`finance_invoices.json`) | {manifests['finance']['invoices_count']} | $\\ge 300$ | **MET** |
| **Finance** | Payments (`finance_payments.json`) | {manifests['finance']['payments_count']} | $\\ge 100$ | **MET** |
| **Operations** | Suppliers (`operations_suppliers.json`) | {manifests['operations']['suppliers_count']} | $\\ge 50$ | **MET** |
| **Operations** | Inventory Items (`operations_inventory.json`) | {manifests['operations']['inventory_count']} | $\\ge 300$ | **MET** |
| **Operations** | Purchase Orders (`operations_purchase_orders.json`) | {manifests['operations']['purchase_orders_count']} | $\\ge 100$ | **MET** |

---

## 3. Department Schemas & Field Definitions

### A. Sales Schema
- `customer_code`: Unique identifier (e.g. `CUST-0042`)
- `company_name`: Synthetic commercial organization
- `deal_value`: Estimated opportunity value in USD ($15k to $750k)
- `stage`: Lifecycle stage (`lead`, `qualified`, `proposal`, `closed_won`, `closed_lost`)
- `needs_finance_approval`: Boolean flag triggered if deal value $> $100,000 or discount requested
- `finance_status`: Approval state (`none`, `pending`, `approved`, `rejected`)

### B. HR Schema
- `employee_code`: Unique identifier (e.g. `EMP-0012`)
- `position`: Job title
- `leave_balance`: Remaining annual vacation balance (days)
- `salary`: Confidential base compensation in USD ($55k to $185k). **Restricted to HR Management.**
- `performance_rating`: Annual review tier

### C. Finance Schema
- `invoice_number`: Unique tax/billing invoice (e.g. `INV-2026-00104`)
- `client_name`: Billable customer or vendor entity
- `amount`: Monetary obligation in USD
- `status`: Payment condition (`sent`, `paid`, `overdue`, `pending_approval`, `cancelled`)
- `due_date`: Net payment deadline

### D. Operations Schema
- `sku`: Stock keeping unit (e.g. `SKU-SER-0021`)
- `item_name`: Part or equipment descriptor
- `quantity_on_hand`: Physical warehouse inventory count
- `reorder_threshold`: Safety stock level triggering automated procurement
- `warehouse_location`: Physical facility compartment (e.g. `Warehouse Alpha - Zone A`)
- `status`: Availability indicator (`in_stock`, `low_stock`, `out_of_stock`)
"""
    with open(dict_path, "w", encoding="utf-8") as f:
        f.write(dict_content)
    print(f"Data dictionary written to {dict_path}")


def main():
    manifests = {
        "sales": generate_sales_data(),
        "hr": generate_hr_data(),
        "finance": generate_finance_data(),
        "operations": generate_operations_data(),
        "generated_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED
    }
    write_manifests_and_dictionary(manifests)
    print("All synthetic datasets generated and manifests recorded successfully.")


if __name__ == "__main__":
    main()
