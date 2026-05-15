"""
ChromaDB singleton client.

Imported by any module that needs direct collection access without going
through the full ingestion pipeline (e.g. the chat/summary routers).
"""

from pathlib import Path
import chromadb

_BASE_DIR       = Path(__file__).resolve().parent.parent.parent   # backend/
CHROMA_PATH     = _BASE_DIR / "data" / "chromadb"
COLLECTION_NAME = "medical_records"

_client: chromadb.PersistentClient | None = None


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return _client


def get_collection() -> chromadb.Collection:
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
