"""
GET /api/patient/{patient_id}
-----------------------------
Queries the medical_records table in PostgreSQL and returns all records for a patient.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.services.patient import get_patient_info_from_id
# from app.schemas.patient import PatientRecords

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["patient"])


@router.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    try:
        patient_info = get_patient_info_from_id(patient_id=patient_id)
    except Exception as e:
        log.error("DB error fetching patient %s: %s", patient_id, e)
        raise HTTPException(status_code=500, detail="Lỗi truy vấn cơ sở dữ liệu")

    if not patient_info:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy bệnh nhân '{patient_id}'")

    return {"patient_id": patient_id, "data": patient_info}
