from .database import db
from sqlalchemy import text


_NULL_VALUES = {"nan", "none", "", "0", "0.0", "0001-01-01 00:00:00"}


def _clean(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in _NULL_VALUES else s

def get_patient_info_from_id(patient_id: str):
    with db._engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM medical_records WHERE ma_bn_an = :pid"),
            {"pid": patient_id.strip()},
        )
        rows = result.mappings().all()
        
    records = [{k: _clean(v) for k, v in row.items()} for row in rows]
    return records[0]
