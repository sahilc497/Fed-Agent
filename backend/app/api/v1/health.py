from typing import Any
from fastapi import APIRouter, Depends
from app.db.session import get_db
from app.services.ollama_service import OllamaService

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "service": "Federated Agentic Mesh Backend"}


@router.get("/health/ready")
async def readiness_check(db: Any = Depends(get_db)):
    """Comprehensive readiness probe for database and local Ollama model."""
    # 1. Database check
    db_status = "unavailable"
    try:
        conn = getattr(db, "conn", db)
        cursor = conn.execute("SELECT 1")
        row = cursor.fetchone()
        if row and (row[0] == 1 or row["1"] == 1 if hasattr(row, "keys") else True):
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Local Ollama check
    ollama = OllamaService()
    ollama_info = await ollama.check_health()

    is_ready = (db_status == "connected")

    return {
        "status": "ready" if is_ready else "not_ready",
        "dependencies": {
            "database": {
                "status": db_status
            },
            "ollama_local_runtime": ollama_info
        }
    }
