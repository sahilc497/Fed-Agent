import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any


class IntentLabel(str, Enum):
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"
    MULTI_DEPARTMENT = "multi_department"
    UNKNOWN = "unknown"


class RouterResult:
    def __init__(self, intent: IntentLabel, confidence: float, explanation: str):
        self.intent = intent
        self.confidence = confidence
        self.explanation = explanation


class BaseIntentRouter(ABC):
    @abstractmethod
    def classify_intent(self, query: str) -> RouterResult:
        """Classifies a user query into one of the 6 canonical intent classes."""
        pass


class RuleBasedIntentRouter(BaseIntentRouter):
    """
    Lightweight, deterministic rule-based router.
    Easily swappable with a locally trained ML classifier in a later phase.
    """
    def __init__(self):
        self.keywords = {
            IntentLabel.OPERATIONS: [
                "operations", "supply chain", "warehouse", "warehouses", "logistics", "shipping", "inventory",
                "inventory tracking", "stock", "stocks", "sku", "skus", "fulfillment", "shipment", "shipments", "backorder", "backorders"
            ],
            IntentLabel.SALES: [
                "sales", "deal", "deals", "pipeline", "lead", "leads", "client", "clients",
                "opportunity", "opportunities", "contract", "contracts", "proposal", "proposals",
                "discount", "discounts", "revenue quota"
            ],
            IntentLabel.HR: [
                "hr", "leave", "leaves", "employee", "employees", "vacation", "vacations", "sick leave",
                "salary", "salaries", "payroll", "benefits", "hiring", "onboarding",
                "pto", "paid time off", "time off"
            ],

            IntentLabel.FINANCE: [
                "finance", "invoice", "invoices", "payment", "payments", "wire", "wires",
                "wire transfer", "wire transfers", "billing", "budget", "budgets", "tax", "overdue", "accounts payable"
            ]
        }

    def classify_intent(self, query: str) -> RouterResult:
        q_lower = query.lower()

        # Special domain check: Scenario B (Opportunities awaiting finance approval is Sales)
        if ("opportunity" in q_lower or "opportunities" in q_lower or "deal" in q_lower) and (
            "awaiting finance" in q_lower or "finance approval" in q_lower or "finance status" in q_lower
        ):
            return RouterResult(
                intent=IntentLabel.SALES,
                confidence=0.92,
                explanation="Sales intent with cross-department Finance approval check."
            )

        # Check matching departments across all 4 departments
        matched_intents = []
        for intent, kw_list in [
            (IntentLabel.SALES, self.keywords[IntentLabel.SALES]),
            (IntentLabel.HR, self.keywords[IntentLabel.HR]),
            (IntentLabel.FINANCE, self.keywords[IntentLabel.FINANCE]),
            (IntentLabel.OPERATIONS, self.keywords[IntentLabel.OPERATIONS]),
        ]:
            if any(re.search(r"\b" + re.escape(w) + r"\b", q_lower) for w in kw_list):
                matched_intents.append(intent)

        # Multi-department check (e.g. Sales + Finance general summary)
        if len(matched_intents) > 1:
            return RouterResult(
                intent=IntentLabel.MULTI_DEPARTMENT,
                confidence=0.90,
                explanation=f"Cross-department query spans: {[m.value for m in matched_intents]}"
            )

        if len(matched_intents) == 1:
            return RouterResult(
                intent=matched_intents[0],
                confidence=0.85,
                explanation=f"Direct match for department {matched_intents[0].value}"
            )

        return RouterResult(
            intent=IntentLabel.UNKNOWN,
            confidence=0.30,
            explanation="No department-specific keywords detected; ambiguous query."
        )
