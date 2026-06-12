"""
POST /api/summary
-----------------
Request  { "ma_bn_an": "BN0052" }
Response { "patient_id", "summary" }

POST /api/refine
----------------
Request  { "ma_bn_an": "BN0052", "summary": "...", "prompt": "..." }
Response { "patient_id", "summary" }

POST /api/preview-html
----------------------
Request  { "ma_bn_an": "BN0052", "summary": "...", <optional patient fields> }
Response  text/html document for browser preview

POST /api/export-docx
---------------------
Request  { "ma_bn_an": "BN0052", "summary": "...", <optional patient fields> }
Response  .docx file download

Errors
  422  missing / invalid request body
  500  LLM or graph execution failure
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from app.services.docx_export import build_docx, fetch_patient_info
from app.services.html_preview import build_preview_html
from app.services.summary_agent.summary_graph import run_refine, run_summary

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

@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(body: SummaryRequest) -> SummaryResponse:
    pid = body.ma_bn_an.strip()
    if not pid:
        raise HTTPException(status_code=422, detail="ma_bn_an must not be empty.")

    log.info("Summary request: patient_id=%s", pid)

    try:
        summary = await run_summary(pid)
    except Exception as exc:
        log.exception("Summary generation failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {exc}")

    return SummaryResponse(patient_id=pid, summary=summary)


@router.post("/refine", response_model=RefineResponse)
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

    try:
        refined = await run_refine(current_summary, instruction)
    except Exception as exc:
        log.exception("Refine failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Refine failed: {exc}")

    return RefineResponse(patient_id=pid, summary=refined)


# ── export ────────────────────────────────────────────────────────────────────

class ExportDocxRequest(BaseModel):
    ma_bn_an:       str           = Field(...,  description="Patient ID")
    summary:        str           = Field(...,  description="Summary text to export")
    patient_name:   Optional[str] = Field(None, description="Họ tên bệnh nhân")
    birthday:       Optional[str] = Field(None, description="Năm sinh")
    age:            Optional[str] = Field(None, description="Tuổi")
    gender:         Optional[str] = Field(None, description="Giới tính (Nam/Nữ)")
    ethnicity:      Optional[str] = Field(None, description="Dân tộc")
    address:        Optional[str] = Field(None, description="Địa chỉ")
    id_number:      Optional[str] = Field(None, description="Số CMND/CCCD")
    admission_date: Optional[str] = Field(None, description="Ngày nhập viện")
    discharge_date: Optional[str] = Field(None, description="Ngày xuất viện")


@router.post("/preview-html", response_class=HTMLResponse)
async def preview_html(body: ExportDocxRequest) -> HTMLResponse:
    pid = body.ma_bn_an.strip()
    summary = body.summary.strip()

    if not pid:
        raise HTTPException(status_code=422, detail="ma_bn_an must not be empty.")
    if not summary:
        raise HTTPException(status_code=422, detail="summary must not be empty.")

    db_info = fetch_patient_info(pid)
    patient_info = {
        "patient_name":   body.patient_name   or db_info.get("patient_name", ""),
        "birthday":       body.birthday       or db_info.get("birthday", ""),
        "age":            body.age            or db_info.get("age", ""),
        "gender":         body.gender         or db_info.get("gender", ""),
        "ethnicity":      body.ethnicity      or "",
        "address":        body.address        or db_info.get("address", ""),
        "id_number":      body.id_number      or db_info.get("id_number", ""),
        "admission_date": body.admission_date or db_info.get("admission_date", ""),
        "discharge_date": body.discharge_date or db_info.get("discharge_date", ""),
    }

    try:
        html = build_preview_html(pid, summary, patient_info)
    except Exception as exc:
        log.exception("HTML preview failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Preview failed: {exc}")

    return HTMLResponse(content=html)


@router.post("/export-docx")
async def export_docx(body: ExportDocxRequest) -> Response:
    pid = body.ma_bn_an.strip()
    summary = body.summary.strip()

    if not pid:
        raise HTTPException(status_code=422, detail="ma_bn_an must not be empty.")
    if not summary:
        raise HTTPException(status_code=422, detail="summary must not be empty.")

    # Fetch DB demographics for any field the caller left as None
    db_info = fetch_patient_info(pid)
    patient_info = {
        "patient_name":   body.patient_name   or db_info.get("patient_name", ""),
        "birthday":       body.birthday       or db_info.get("birthday", ""),
        "age":            body.age            or db_info.get("age", ""),
        "gender":         body.gender         or db_info.get("gender", ""),
        "ethnicity":      body.ethnicity      or "",
        "address":        body.address        or db_info.get("address", ""),
        "id_number":      body.id_number      or db_info.get("id_number", ""),
        "admission_date": body.admission_date or db_info.get("admission_date", ""),
        "discharge_date": body.discharge_date or db_info.get("discharge_date", ""),
    }

    try:
        docx_bytes = build_docx(pid, summary, patient_info)
    except Exception as exc:
        log.exception("DOCX export failed for patient %s", pid)
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")

    filename = f"tom_tat_{pid}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
