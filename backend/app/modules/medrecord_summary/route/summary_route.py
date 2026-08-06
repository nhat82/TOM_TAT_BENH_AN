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

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import opik

from app.modules.medrecord_summary.services.agent_summary import summary_agent
from app.agents.masking import (
    get_vault,
    masking_context,
    remask_text,
    unmask_text,
)
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

    input_state = {
        "patient_id": pid,
        "messages": [{"role": "user", "content": f"Generate the medical summary for patient {pid}."}],
    }
    config = {
        "configurable": {"thread_id": pid},
        "callbacks": [get_opik_tracer(agent="summary-agent", thread_id=pid, patient_id=pid, endpoint="summary")],
    }

    vault = get_vault(pid)
    try:
        with masking_context(vault):
            result = await summary_agent.ainvoke(input_state, config=config)
        summary = unmask_text(_extract_text(result["messages"][-1].content), vault)
    except Exception as exc:
        log.exception("Summary generation failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {exc}")

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

    # Same vault as /summary — the incoming text carries its placeholders.
    vault = get_vault(pid)
    # The summary was exposed to the user; strip PII again before it re-enters
    # the model context.
    current_summary = remask_text(current_summary, vault)

    input_state = {
        "patient_id": pid,
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
    config = {
        "configurable": {"thread_id": f"{pid}-refine"},
        "callbacks": [
            get_opik_tracer(agent="summary-agent", thread_id=f"{pid}-refine", patient_id=pid, endpoint="refine")
        ],
    }

    try:
        with masking_context(vault):
            result = await summary_agent.ainvoke(input_state, config=config)
        refined = unmask_text(_extract_text(result["messages"][-1].content), vault)
    except Exception as exc:
        log.exception("Refine failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Refine failed: {exc}")

    return RefineResponse(patient_id=pid, summary=refined)
