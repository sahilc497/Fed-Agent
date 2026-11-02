# Synthetic Enterprise Datasets — Data Dictionary & Specification

> **NOTICE:** All data contained in these datasets is **100% synthetically generated** for demonstration, benchmarking, and access evaluation purposes. No real human, financial, or company records are used.

## 1. Dataset Generation Manifest
- **Generator Random Seed:** `20260421` (Deterministic & Reproducible)
- **Generated At:** `2026-10-21T17:16:04.124132+00:00`
- **Checksums:**
  - Sales Opportunities: `68f7bf18972b8b99c4d031e751a044a342aa195f02006ae536eb00987f416e22`
  - HR Employees: `d5e570efc3dde26d09bb405b33c22ae32bbfc9c590a20c04875971d6f1f2785a`
  - Finance Invoices: `169d1587ae72532f311605636eeb3dc0adc0a9c842c4de1b0511e38e373576db`
  - Operations Inventory: `bb068bcf10d3b8ddb297cbda8aaa3a1a4e135d9f5cd5d304860b6265d177761a`

## 2. Structured Record Counts Summary

| Department | Primary Entities | Record Count | Minimum Requirement | Compliance Status |
| :--- | :--- | :--- | :--- | :--- |
| **Sales** | Customers (`sales_customers.json`) | 120 | $\ge 100$ | **MET** |
| **Sales** | Opportunities (`sales_opportunities.json`) | 550 | $\ge 500$ | **MET** |
| **HR** | Employees (`hr_employees.json`) | 160 | $\ge 150$ | **MET** |
| **HR** | Leave Requests (`hr_leaves.json`) | 240 | $\ge 200$ | **MET** |
| **Finance** | Vendors (`finance_vendors.json`) | 110 | $\ge 100$ | **MET** |
| **Finance** | Invoices (`finance_invoices.json`) | 350 | $\ge 300$ | **MET** |
| **Finance** | Payments (`finance_payments.json`) | 160 | $\ge 100$ | **MET** |
| **Operations** | Suppliers (`operations_suppliers.json`) | 60 | $\ge 50$ | **MET** |
| **Operations** | Inventory Items (`operations_inventory.json`) | 320 | $\ge 300$ | **MET** |
| **Operations** | Purchase Orders (`operations_purchase_orders.json`) | 120 | $\ge 100$ | **MET** |

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
