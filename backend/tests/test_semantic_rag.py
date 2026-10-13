import pytest
from app.rag.embeddings import (
    get_embedding_service,
    reset_embedding_service,
    SentenceTransformersEmbeddingService,
    LocalDeterministicEmbeddingService,
    EmbeddingModelUnavailableError,
    compute_cosine_similarity
)
from app.core.config import settings


def test_sentence_transformers_semantic_properties():
    reset_embedding_service()
    service = SentenceTransformersEmbeddingService()
    assert service.dimension == 384
    assert "all-MiniLM-L6-v2" in service.model_name

    doc = "Enterprise sales proposals require approval from finance."
    q_similar = "Do sales deals need financial approval?"
    q_unrelated = "What is the policy for annual vacation days in human resources?"

    emb_doc = service.embed_text(doc)
    emb_sim = service.embed_text(q_similar)
    emb_unrel = service.embed_text(q_unrelated)

    assert len(emb_doc) == 384
    assert len(emb_sim) == 384
    assert len(emb_unrel) == 384

    sim_score = compute_cosine_similarity(emb_doc, emb_sim)
    unrel_score = compute_cosine_similarity(emb_doc, emb_unrel)

    # Paraphrased query should rank significantly higher than unrelated query
    assert sim_score > 0.50
    assert sim_score > unrel_score + 0.30


def test_no_silent_fallback_on_invalid_provider(monkeypatch):
    reset_embedding_service()
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "non_existent_provider_xyz")
    with pytest.raises(EmbeddingModelUnavailableError) as exc_info:
        get_embedding_service()
    assert "Unsupported or unrecognized EMBEDDING_PROVIDER" in str(exc_info.value)
    reset_embedding_service()


def test_missing_sentence_transformers_model_raises_clear_error(monkeypatch):
    reset_embedding_service()
    # If a non-existent local model is requested with downloads disabled
    monkeypatch.setattr(settings, "ALLOW_MODEL_DOWNLOADS", False)
    with pytest.raises(EmbeddingModelUnavailableError) as exc_info:
        SentenceTransformersEmbeddingService(model_name_or_path="completely-missing-model-name-12345")
    assert "Failed to load local semantic embedding model" in str(exc_info.value)
    reset_embedding_service()


@pytest.mark.asyncio
async def test_semantic_retrieval_service_filters(db_session):
    from sqlalchemy import select
    from app.db.models.department import Department
    from app.rag.retrieval import RAGRetrievalService
    from app.db.models.document import Document, DocumentChunk

    sales_dept = (await db_session.execute(select(Department).where(Department.code == "sales"))).scalars().first()
    hr_dept = (await db_session.execute(select(Department).where(Department.code == "hr"))).scalars().first()

    reset_embedding_service()
    embedder = get_embedding_service()

    # Create test docs
    doc_sales = Document(
        title="Sales Discount Guidelines",
        filename="sales_discount.txt",
        file_path="data/sales_discount.txt",
        file_type="txt",
        department_id=sales_dept.id,
        access_level="internal",
        uploaded_by=1,
        status="indexed"
    )
    doc_hr = Document(
        title="HR Secret Compensation",
        filename="hr_secret.txt",
        file_path="data/hr_secret.txt",
        file_type="txt",
        department_id=hr_dept.id,
        access_level="confidential",
        uploaded_by=1,
        status="indexed"
    )
    db_session.add_all([doc_sales, doc_hr])
    await db_session.flush()

    content_sales = "Sales representatives can grant discounts up to ten percent before finance review."
    content_hr = "Executive compensation packages are strictly confidential."

    chunk_sales = DocumentChunk(
        document_id=doc_sales.id,
        chunk_index=0,
        content=content_sales,
        department_id=sales_dept.id,
        access_level="internal",
        embedding=embedder.embed_text(content_sales)
    )
    chunk_hr = DocumentChunk(
        document_id=doc_hr.id,
        chunk_index=0,
        content=content_hr,
        department_id=hr_dept.id,
        access_level="confidential",
        embedding=embedder.embed_text(content_hr)
    )
    db_session.add_all([chunk_sales, chunk_hr])
    await db_session.commit()

    retriever = RAGRetrievalService(db_session)

    # 1. Query sales department with allowed access ["public", "internal"]
    results = await retriever.retrieve_evidence(
        query="What discount can a sales rep offer?",
        department_id=sales_dept.id,
        department_code="sales",
        allowed_access_levels=["public", "internal"]
    )
    assert len(results) >= 1
    assert any("discount" in r.snippet.lower() for r in results)
    assert results[0].confidence >= 0.50

    # 2. Query HR department with only ["public", "internal"] -> confidential chunk must NOT be returned
    results_hr = await retriever.retrieve_evidence(
        query="What are the executive compensation packages?",
        department_id=hr_dept.id,
        department_code="hr",
        allowed_access_levels=["public", "internal"]
    )
    assert not any("executive compensation" in r.snippet.lower() for r in results_hr)

    # 3. Cross-department query: HR query to sales department -> no HR chunks should ever appear
    results_cross = await retriever.retrieve_evidence(
        query="Tell me about executive compensation",
        department_id=sales_dept.id,
        department_code="sales",
        allowed_access_levels=["public", "internal", "confidential"]
    )
    for r in results_cross:
        assert "executive compensation" not in r.snippet.lower()
