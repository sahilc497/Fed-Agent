import os
import sys
import asyncio
import logging

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.document import DocumentChunk
from app.rag.embeddings import get_embedding_service, reset_embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reembed_chunks")


async def reembed_all():
    reset_embedding_service()
    embedder = get_embedding_service()
    logger.info(f"Using embedding service: {embedder.model_name} (dimension: {embedder.dimension})")

    async with AsyncSessionLocal() as session:
        stmt = select(DocumentChunk).order_by(DocumentChunk.id)
        result = await session.execute(stmt)
        chunks = result.scalars().all()

        if not chunks:
            logger.info("No document chunks found in database.")
            return

        logger.info(f"Re-embedding {len(chunks)} chunks in the database...")
        for ch in chunks:
            new_vec = embedder.embed_text(ch.content)
            ch.embedding = new_vec

        await session.commit()
        logger.info(f"Successfully updated {len(chunks)} document chunks with new embeddings from {embedder.model_name}!")


if __name__ == "__main__":
    asyncio.run(reembed_all())
