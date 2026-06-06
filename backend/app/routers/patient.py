"""
GET /api/patient/{patient_id}
-----------------------------
Queries the medical_records table in PostgreSQL and returns all records for a patient.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.services.database import db

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["patient"])

_NULL_VALUES = {"nan", "none", "", "0", "0.0", "0001-01-01 00:00:00"}


def _clean(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in _NULL_VALUES else s


@router.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    try:
        with db._engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM medical_records WHERE ma_bn_an = :pid"),
                {"pid": patient_id.strip()},
            )
            rows = result.mappings().all()
    except Exception as e:
        log.error("DB error fetching patient %s: %s", patient_id, e)
        raise HTTPException(status_code=500, detail="Lỗi truy vấn cơ sở dữ liệu")

    if not rows:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy bệnh nhân '{patient_id}'")

    records = [{k: _clean(v) for k, v in row.items()} for row in rows]

    return {"patient_id": patient_id, "data": records[0] if len(records) == 1 else records}
