"""
POST /api/ingest
----------------
Request  { "force": false }   (optional)
Response { "added": int, "skipped": int }

Triggers the CSV ingestion pipeline from app.services.ingest.
Runs in a thread pool so it doesn't block the event loop during embedding.
"""

from __future__ import annotations

import logging
from asyncio import get_event_loop

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ingest import DEFAULT_CSV, ingest_csv

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["ingest"])


class IngestRequest(BaseModel):
    force: bool = Field(False, description="Re-embed all records even if unchanged")


class IngestResponse(BaseModel):
    added: int
    skipped: int


@router.post("/ingest", response_model=IngestResponse)
async def run_ingest(body: IngestRequest = IngestRequest()) -> IngestResponse:
    """
    Ingest the default CSV into ChromaDB.
    Skips records whose content hash hasn't changed unless force=True.
    """
    if not DEFAULT_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail=f"CSV not found: {DEFAULT_CSV}",
        )

    try:
        loop = get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: ingest_csv(DEFAULT_CSV, body.force)
        )
    except Exception as exc:
        log.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")

    return IngestResponse(**result)
