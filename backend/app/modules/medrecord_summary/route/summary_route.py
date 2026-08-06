"""
POST /api/summary
-----------------
Request  { "ma_bn_an": "BN0052" }
Response { "patient_id", "summary" }

POST /api/refine
----------------
Request  { "ma_bn_an": "BN0052", "summary": "...", "prompt": "..." }
Response { "patient_id", "summary" }

Errors
  422  missing / invalid request body
  500  LLM or graph execution failure
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import opik

from app.modules.medrecord_summary.services.agent_summary import summary_agent
from app.core.security import pii_masker
from app.agents.tracing import get_opik_tracer

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["summary"])


# ── schemas ───────────────────────────────────────────────────────────────────

class SummaryRequest(BaseModel):
    ma_bn_an: str = Field(..., examples=["BN0052"], description="Patient ID")


class SummaryResponse(BaseModel):
    patient_id: str
    summary: str


class RefineRequest(BaseModel):
    ma_bn_an: str = Field(..., examples=["BN0052"], description="Patient ID")
    summary: str = Field(..., description="Current summary to refine")
    prompt: str = Field(..., description="Refinement instruction from user")


class RefineResponse(BaseModel):
    patient_id: str
    summary: str


# ── endpoints ─────────────────────────────────────────────────────────────────

def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return str(content)


@router.post("/summary", response_model=SummaryResponse)
@opik.track(name="generate_summary")
async def generate_summary(body: SummaryRequest) -> SummaryResponse:
    pid = body.ma_bn_an.strip()
    if not pid:
        raise HTTPException(status_code=422, detail="ma_bn_an must not be empty.")

    log.info("Summary request: patient_id=%s", pid)

    message_key = f"{pid}:{datetime.now().isoformat()}"
    input_state = {
        "patient_id": pid,
        "message_key": message_key,
        "messages": [{"role": "user", "content": f"Generate the medical summary for patient {pid}."}],
    }
    tracer = get_opik_tracer(agent="summary-agent", thread_id=pid, patient_id=pid, endpoint="summary")
    config = {
        "configurable": {"thread_id": pid},
        "callbacks": [tracer] if tracer else [],
    }

    try:
        result = await summary_agent.ainvoke(input_state, config=config)
        summary = pii_masker.unmask(message_key, _extract_text(result["messages"][-1].content))
    except Exception as exc:
        log.exception("Summary generation failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {exc}")
    finally:
        pii_masker.forget(message_key)

    return SummaryResponse(patient_id=pid, summary=summary)


@router.post("/refine", response_model=RefineResponse)
@opik.track(name="refine_patient_summary")
async def refine_patient_summary(body: RefineRequest) -> RefineResponse:
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

    message_key = f"{pid}:{datetime.now().isoformat()}"
    input_state = {
        "patient_id": pid,
        "message_key": message_key,
        "current_summary": current_summary,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Refine the following summary according to this instruction: {instruction}\n\n"
                    f"Current summary:\n{current_summary}"
                ),
            }
        ],
    }
    tracer = get_opik_tracer(agent="summary-agent", thread_id=f"{pid}-refine", patient_id=pid, endpoint="refine")
    config = {
        "configurable": {"thread_id": f"{pid}-refine"},
        "callbacks": [tracer] if tracer else [],
    }

    try:
        result = await summary_agent.ainvoke(input_state, config=config)
        refined = pii_masker.unmask(message_key, _extract_text(result["messages"][-1].content))
    except Exception as exc:
        log.exception("Refine failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Refine failed: {exc}")
    finally:
        pii_masker.forget(message_key)

    return RefineResponse(patient_id=pid, summary=refined)
