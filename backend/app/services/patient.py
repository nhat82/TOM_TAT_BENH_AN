from app.core.database import engine
from sqlalchemy import text


_NULL_VALUES = {"nan", "none", "", "0", "0.0", "0001-01-01 00:00:00"}


def _clean(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in _NULL_VALUES else s

def get_all_patients():
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT ma_bn_an, birthdayyear,
                       departmentid, medicalrecorddate_in, medicalrecorddate_out,
                       chandoan_out_main, chandoan_in
                FROM ai_benh_an_so
                ORDER BY medicalrecorddate_in DESC
            """)
        )
        rows = result.mappings().all()
    return [{k: _clean(v) for k, v in row.items()} for row in rows]

def get_patient_info_from_id(patient_id: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM ai_benh_an_so WHERE ma_bn_an = :pid"),
            {"pid": patient_id.strip()},
        )
        row = result.mappings().first()
    
    if not row: 
        return None
    record = {k: _clean(v) for k, v in row.items()}
    return record
