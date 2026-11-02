import os
import sys
import asyncio
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db.sqlite import create_connection, db_transaction
from app.db.schema import init_db
from app.rag.ingestion import DocumentIngestionService
from app.repositories.user_repo import DepartmentRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("index_corpus")


async def index_all():
    init_db()
    kb_dir = BASE_DIR / "data" / "knowledge_base"
    dept_map = {"sales": 1, "hr": 2, "finance": 3, "operations": 4}

    conn = create_connection()
    ingest_svc = DocumentIngestionService(conn)

    # Clean existing documents to avoid duplicate chunks on re-index
    cursor = conn.cursor()
    cursor.execute("DELETE FROM document_chunks;")
    cursor.execute("DELETE FROM documents;")
    conn.commit()

    total_docs = 0
    total_chunks = 0

    for dept_code, dept_id in dept_map.items():
        dept_folder = kb_dir / dept_code
        if not dept_folder.exists():
            continue

        for file_path in dept_folder.glob("*.txt"):
            filename = file_path.name
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse title and access level from header
            lines = content.split("\n")
            title = lines[0].replace("#", "").strip() if lines else filename
            access_level = "internal"
            for line in lines[:8]:
                if line.startswith("Access Level:"):
                    access_level = line.split(":", 1)[1].strip().lower()

            doc = await ingest_svc.ingest_document(
                title=title,
                filename=filename,
                file_bytes=content.encode("utf-8"),
                file_type="txt",
                department_id=dept_id,
                access_level=access_level,
                uploaded_by_id=1  # Admin
            )
            total_docs += 1

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM document_chunks;")
    total_chunks = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM documents;")
    stored_docs = cursor.fetchone()[0]
    conn.close()

    logger.info(f"Indexing complete! Successfully indexed {stored_docs} documents and created {total_chunks} embedded vector chunks in SQLite.")


if __name__ == "__main__":
    asyncio.run(index_all())
