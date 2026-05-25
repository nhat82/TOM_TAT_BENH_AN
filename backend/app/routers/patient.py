"""
GET /api/patient/{patient_id}
-----------------------------
Reads directly from the CSV file and returns all columns for a patient.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["patient"])

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_CSV_PATH = _BASE_DIR / "data" / "Sample_20BN.csv"

_NULL_VALUES = {"nan", "none", "", "0", "0.0", "0001-01-01 00:00:00"}


def _clean(val: str) -> str:
    s = str(val).strip()
    return "" if s.lower() in _NULL_VALUES else s


@router.get("/patient/{patient_id}")
async def get_patient(patient_id: str):
    if not _CSV_PATH.exists():
        raise HTTPException(status_code=500, detail="Không tìm thấy file dữ liệu CSV")

    df = pd.read_csv(_CSV_PATH, skiprows=[1], dtype=str)
    df.fillna("", inplace=True)

    mask = df["ma_bn_an"].str.strip() == patient_id.strip()
    matches = df[mask]

    if matches.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy bệnh nhân '{patient_id}'")

    row = matches.iloc[0].to_dict()
    data = {k: _clean(v) for k, v in row.items()}

    return {"patient_id": patient_id, "data": data}
