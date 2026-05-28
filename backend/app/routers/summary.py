"""
POST /api/summary
-----------------
Request  { "ma_bn_an": "BN0052" }
Response { "patient_id", "summary", "timeline", "chunks_used" }

Errors
  404  patient not found in ChromaDB (run ingest first)
  422  missing / invalid request body
  500  LLM or graph execution failure
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.graphs.summary_graph import summary_graph, refine_summary
from app.graphs.summary_graph import _split_into_chunks, _rerank_chunks
from app.services.chroma import get_collection

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["summary"])


# ── schemas ───────────────────────────────────────────────────────────────────

class SummaryRequest(BaseModel):
    ma_bn_an: str = Field(..., examples=["BN0052"], description="Patient ID")


class RefineHistoryEntry(BaseModel):
    instruction: str
    result_summary: str


class RefineRequest(BaseModel):
    ma_bn_an: str = Field(..., examples=["BN0052"], description="Patient ID")
    summary: str = Field(..., description="Current summary to refine")
    prompt: str = Field(..., description="Refinement instruction from user")
    history: list[RefineHistoryEntry] = Field(
        default_factory=list,
        description="Prior refinement turns, oldest first",
    )


class RefineResponse(BaseModel):
    patient_id: str
    summary: str


class TimelineEvent(BaseModel):
    date: str
    event: str
    detail: str


class SummaryResponse(BaseModel):
    patient_id: str
    summary: str
    timeline: list[TimelineEvent]
    chunks_used: int


# ── endpoint ──────────────────────────────────────────────────────────────────

@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(body: SummaryRequest) -> SummaryResponse:
    """
    Run the RAG summary graph for a single patient.

    The graph pipeline:
      retrieve → build_timeline → draft_summary
    """
    pid = body.ma_bn_an.strip()
    if not pid:
        raise HTTPException(status_code=422, detail="ma_bn_an must not be empty.")

    log.info("Summary request: patient_id=%s", pid)

    try:
        result: dict = await summary_graph.ainvoke({"patient_id": pid})
    except ValueError as exc:
        # Patient not found in ChromaDB
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        log.exception("Graph execution failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {exc}")

    # Normalise timeline rows — the LLM may omit keys
    timeline = [
        TimelineEvent(
            date=str(item.get("date", "")),
            event=str(item.get("event", "")),
            detail=str(item.get("detail", "")),
        )
        for item in (result.get("timeline") or [])
    ]

    return SummaryResponse(
        patient_id=pid,
        summary=result.get("draft", ""),
        timeline=timeline,
        chunks_used=len(result.get("chunks", [])),
    )


@router.post("/refine", response_model=RefineResponse)
async def refine_patient_summary(body: RefineRequest) -> RefineResponse:
    """
    Refine an existing summary based on a user instruction.

    Optionally retrieves original chunks from ChromaDB for grounding.
    """
    pid = body.ma_bn_an.strip()
    instruction = body.prompt.strip()
    current_summary = body.summary.strip()

    if not pid:
        raise HTTPException(status_code=422, detail="ma_bn_an must not be empty.")
    if not instruction:
        raise HTTPException(status_code=422, detail="prompt must not be empty.")
    if not current_summary:
        raise HTTPException(status_code=422, detail="summary must not be empty.")

    log.info("Refine request: patient_id=%s instruction=%.60s", pid, instruction)

    # Fetch original chunks for grounding (best-effort; refinement works without them)
    chunks: list[str] | None = None
    try:
        collection = get_collection()
        result = collection.get(ids=[pid], include=["documents"])
        if result["documents"] and result["documents"][0]:
            raw = _split_into_chunks(result["documents"][0])
            chunks = _rerank_chunks(instruction, raw, top_n=6)
    except Exception:
        pass

    history = [e.model_dump() for e in body.history]

    try:
        refined = await refine_summary(current_summary, instruction, chunks, history)
    except Exception as exc:
        log.exception("Refine failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Refine failed: {exc}")

    return RefineResponse(patient_id=pid, summary=refined)
