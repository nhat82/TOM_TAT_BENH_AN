"""
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
  500  export generation failure
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from app.modules.medrecord_export.services.docx_export import build_docx, fetch_patient_info
from app.modules.medrecord_export.services.html_preview import build_preview_html

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["export"])


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


def _merge_patient_info(body: ExportDocxRequest, db_info: dict) -> dict:
    patient_info = {**db_info}
    if body.patient_name:   patient_info["ho_ten"] = body.patient_name
    if body.age:            patient_info["age"] = body.age
    if body.gender:         patient_info["gender"] = body.gender
    if body.ethnicity:      patient_info["ethnicity"] = body.ethnicity
    if body.address:        patient_info["dm_tinhcode"] = body.address
    if body.id_number:      patient_info["cccd"] = body.id_number
    if body.admission_date: patient_info["medicalrecorddate_in"] = body.admission_date
    if body.discharge_date: patient_info["medicalrecorddate_out"] = body.discharge_date
    return patient_info


@router.post("/preview-html", response_class=HTMLResponse)
async def preview_html(body: ExportDocxRequest) -> HTMLResponse:
    pid = body.ma_bn_an.strip()
    summary = body.summary.strip()

    if not pid:
        raise HTTPException(status_code=422, detail="ma_bn_an must not be empty.")
    if not summary:
        raise HTTPException(status_code=422, detail="summary must not be empty.")

    db_info = fetch_patient_info(pid)
    patient_info = _merge_patient_info(body, db_info)

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

    db_info = fetch_patient_info(pid)
    patient_info = _merge_patient_info(body, db_info)

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
