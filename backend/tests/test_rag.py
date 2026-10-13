import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.ingestion import DocumentIngestionService
from app.rag.retrieval import RAGRetrievalService


@pytest.mark.asyncio
async def test_document_ingestion_and_retrieval(db_session: AsyncSession):
    ingest = DocumentIngestionService(db_session)
    retrieval = RAGRetrievalService(db_session)

    test_content = b"The enterprise Q4 product launch roadmap requires all engineering teams to complete compliance reviews."
    doc = await ingest.ingest_document(
        title="Q4 Product Launch Plan",
        filename="product_launch.txt",
        file_bytes=test_content,
        file_type="txt",
        department_id=1,  # Sales
        access_level="internal",
        uploaded_by_id=1
    )
    assert doc.id is not None
    assert doc.status == "indexed"

    # Search for sales department
    evidence = await retrieval.retrieve_evidence(
        query="compliance reviews roadmap",
        department_id=1,
        department_code="sales",
        top_k=3
    )
    assert len(evidence) > 0
    assert any("compliance reviews" in e.snippet for e in evidence)


@pytest.mark.asyncio
async def test_department_rag_isolation(db_session: AsyncSession):
    retrieval = RAGRetrievalService(db_session)

    # Query HR department using a term from Sales
    # Sales doc in dept 1 shouldn't appear in HR dept 2 retrieval!
    evidence = await retrieval.retrieve_evidence(
        query="Q4 Enterprise Discounting & Pricing Authority Matrix",
        department_id=2,  # HR
        department_code="hr",
        top_k=5
    )
    for e in evidence:
        assert e.department == "hr"
        assert "Discounting & Pricing" not in e.snippet
