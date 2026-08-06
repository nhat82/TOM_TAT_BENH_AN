from app.core.database import engine
from app.utils.type_formatter import format_value
from sqlalchemy import text


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
    return [{k: format_value(v) for k, v in row.items()} for row in rows]

def get_patient_info_from_id(patient_id: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM ai_benh_an_so WHERE ma_bn_an = :pid"),
            {"pid": patient_id.strip()},
        )
        row = result.mappings().first()
    
    if not row: 
        return None
    record = {k: format_value(v) for k, v in row.items()}
    return record
