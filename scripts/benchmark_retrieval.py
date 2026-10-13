import os
import sys
import asyncio
import logging

# Ensure backend root is on sys.path and load backend/.env
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

from app.db.session import AsyncSessionLocal
from app.rag.retrieval import RAGRetrievalService
from app.rag.embeddings import get_embedding_service, reset_embedding_service
from app.db.models import Department
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retrieval_benchmark")


async def run_benchmark():
    reset_embedding_service()
    embedder = get_embedding_service()
    print("=" * 70)
    print("SEMANTIC RETRIEVAL BENCHMARK & EVALUATION")
    print(f"Active Provider: {embedder.__class__.__name__}")
    print(f"Active Model:    {embedder.model_name} (dimension: {embedder.dimension})")
    print("=" * 70)

    async with AsyncSessionLocal() as session:
        # Load department IDs
        sales_dept = (await session.execute(select(Department).where(Department.code == "sales"))).scalar_one()
        hr_dept = (await session.execute(select(Department).where(Department.code == "hr"))).scalar_one()
        finance_dept = (await session.execute(select(Department).where(Department.code == "finance"))).scalar_one()

        retrieval_service = RAGRetrievalService(session)

        test_cases = [
            {
                "name": "Sales Discount Threshold - Paraphrase 1",
                "query": "What discount percentage requires mandatory finance sign-off?",
                "dept_id": sales_dept.id,
                "dept_code": "sales",
                "expected_keyword": "10% and 25%",
                "expected_min_score": 0.45
            },
            {
                "name": "Sales Discount Threshold - Paraphrase 2",
                "query": "How much pricing concession can an account executive give before seeking approval?",
                "dept_id": sales_dept.id,
                "dept_code": "sales",
                "expected_keyword": "discount",
                "expected_min_score": 0.35
            },
            {
                "name": "HR Sick Leave & PTO Policy",
                "query": "How many days off can employees take for medical reasons with a doctor note?",
                "dept_id": hr_dept.id,
                "dept_code": "hr",
                "expected_keyword": "Sick leave",
                "expected_min_score": 0.40
            },
            {
                "name": "Finance Wire Payment Authorization",
                "query": "What is the dollar threshold for outgoing bank transfers requiring dual authorization?",
                "dept_id": finance_dept.id,
                "dept_code": "finance",
                "expected_keyword": "$5,000",
                "expected_min_score": 0.45
            },
            {
                "name": "Department Isolation Test - HR Query to Sales Index",
                "query": "How many vacation days do staff members get per year?",
                "dept_id": sales_dept.id,
                "dept_code": "sales",
                "must_not_contain": "annual leave",
                "is_isolation_check": True
            },
            {
                "name": "Access Control Test - Internal user query for Confidential HR Policy",
                "query": "What are executive stock equity vesting schedules and board compensation?",
                "dept_id": hr_dept.id,
                "dept_code": "hr",
                "allowed_access_levels": ["public", "internal"],  # User only has 'internal' access, confidential is excluded
                "must_not_contain": "Executive equity grant",
                "is_isolation_check": True
            }
        ]

        passed = 0
        total = len(test_cases)

        for tc in test_cases:
            print(f"\n--- Test: {tc['name']} ---")
            print(f"Query: \"{tc['query']}\"")
            print(f"Target Dept: {tc['dept_code']} (ID: {tc['dept_id']})")

            allowed_levels = tc.get("allowed_access_levels", ["public", "internal"])
            results = await retrieval_service.retrieve_evidence(
                query=tc["query"],
                department_id=tc["dept_id"],
                department_code=tc["dept_code"],
                allowed_access_levels=allowed_levels,
                top_k=3,
                similarity_threshold=0.10
            )

            if tc.get("is_isolation_check"):
                forbidden_matched = False
                for r in results:
                    must_not = tc.get("must_not_contain", "")
                    if must_not.lower() in r.snippet.lower():
                        forbidden_matched = True
                        break
                if forbidden_matched:
                    print(f"FAILED: Unauthorized or isolated content leaked into results!")
                else:
                    print(f"PASSED: Department/Access isolation verified! No leakage (results: {len(results)}).")
                    passed += 1
            else:
                if not results:
                    print("FAILED: No documents retrieved!")
                    continue

                top = results[0]
                print(f"Top Result Confidence: {top.confidence:.3f}")
                print(f"Top Snippet: {top.snippet[:120]}...")
                
                has_expected = tc["expected_keyword"].lower() in top.snippet.lower()
                score_ok = top.confidence >= tc["expected_min_score"]

                if has_expected and score_ok:
                    print(f"PASSED: Expected keyword found and confidence ({top.confidence}) >= {tc['expected_min_score']}.")
                    passed += 1
                else:
                    print(f"FAILED: Keyword match={has_expected}, score {top.confidence} >= {tc['expected_min_score']}={score_ok}")

        print("\n" + "=" * 70)
        print(f"BENCHMARK SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print("=" * 70)
        assert passed == total, f"Benchmark failed: only {passed}/{total} tests passed."


if __name__ == "__main__":
    asyncio.run(run_benchmark())
