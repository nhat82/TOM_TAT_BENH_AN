"""
Build a formatted DOCX from a Vietnamese medical summary using the official
Mẫu số 03 — Bản Tóm Tắt Hồ Sơ Bệnh Án docxtpl template.
"""
from __future__ import annotations

import io
import json
import logging
import os
from datetime import date

from docxtpl import DocxTemplate
from sqlalchemy import text

from app.core.database import db
from app.utils.type_formatter import format_date, format_value

log = logging.getLogger(__name__)

TEMPLATE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "mau_so_03.docx")
)

_NARRATIVE_KEYS = [
    "chandoan_in_icd10",
    "chandoan_out_main_icd10",
    "chandoan_in",
    "chandoan_out_main",
    "lydodenkham",
    "tom_tat_qua_trinh_dien_bien",
    "tien_su_benh",
    "dau_hieu_chinh",
    "tom_tat_ket_qua",
    "pttt",
    "tinh_trang_ra_vien",
    "huongdieutri_out",
]


def _parse_summary_json(summary: str) -> dict:
    """Extract narrative template fields from the LLM JSON summary string."""
    try:
        data = json.loads(summary)
        if isinstance(data, dict):
            return {k: str(data.get(k, "") or "") for k in _NARRATIVE_KEYS}
    except (json.JSONDecodeError, TypeError):
        pass
    return {k: "" for k in _NARRATIVE_KEYS}


def fetch_patient_info(pid: str) -> dict:
    """Query ai_benh_an_so for all Mẫu số 03 template fields."""
    try:
        with db._engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM ai_benh_an_so WHERE ma_bn_an = :pid LIMIT 1"),
                {"pid": pid},
            )
            row = result.mappings().first()
    except Exception:
        log.warning("Could not fetch patient info for %s", pid)
        return {}

    if not row:
        return {}

    gender_map = {"1": "Nam", "2": "Nữ"}
    birth_year = format_value(row.get("birthdayyear", ""))
    birthday_full = format_value(row.get("birthday", ""))
    formatted_birthday = format_date(birthday_full) if birthday_full else birth_year

    age = ""
    if birth_year:
        try:
            age = str(date.today().year - int(birth_year))
        except ValueError:
            pass

    gender_raw = format_value(row.get("dm_gioitinhid", ""))
    gender = gender_map.get(gender_raw, gender_raw)

    return {
        "ho_ten":                 format_value(row.get("ho_ten", ""))                  or "",
        "formatted_birthday":      formatted_birthday                              or "",
        "age":                     age,
        "gender":                  gender,
        "ethnicity":               format_value(row.get("dm_dantoc", ""))               or "",
        "dm_tinhcode":             format_value(row.get("dm_tinhcode", ""))             or "",
        "isbn_ut":                 format_value(row.get("isbn_ut", ""))                 or "",
        "cccd":                    format_value(row.get("cccd", ""))                    or "",
        "medicalrecorddate_in":    format_date(row.get("medicalrecorddate_in"))     or "",
        "medicalrecorddate_out":   format_date(row.get("medicalrecorddate_out"))    or "",
        "chandoan_in":             format_value(row.get("chandoan_in", ""))             or "",
        "chandoan_in_icd10":       format_value(row.get("chandoan_in_icd10", ""))       or "",
        "chandoan_out_main":       format_value(row.get("chandoan_out_main", ""))       or "",
        "chandoan_out_main_icd10": format_value(row.get("chandoan_out_main_icd10", "")) or "",
        "lydodenkham":             format_value(row.get("lydodenkham", ""))             or "",
        "departmentid":            format_value(row.get("departmentid", ""))            or "",
        "pttt":                    format_value(row.get("pttt", ""))                    or "",
        "huongdieutri_out":        format_value(row.get("huongdieutri_out", ""))        or "",
        # Legacy keys used by existing callers
        "patient_name":            format_value(row.get("ho_ten", ""))                  or "",
        "birthday":                birth_year                                      or "",
        "id_number":               format_value(row.get("cccd", ""))                    or "",
        "province":                format_value(row.get("dm_tinhcode", ""))             or "",
        "admission_date":          format_date(row.get("medicalrecorddate_in"))     or "",
        "discharge_date":          format_date(row.get("medicalrecorddate_out"))    or "",
    }


def build_docx(patient_id: str, summary: str, patient_info: dict | None = None) -> bytes:
    """
    Fill Mẫu số 03 template with patient data and return DOCX bytes.
    patient_info must come from fetch_patient_info(). LLM narrative fields
    are parsed from the JSON summary string.
    """
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(
            f"DOCX template not found: {TEMPLATE_PATH}\n"
            "Save backend/data/MAU SO 03-PHU LUC II-25-2025-TT-BYT.doc "
            "as backend/data/mau_so_03.docx first."
        )

    db_info = patient_info or {}
    llm = _parse_summary_json(summary)

    context = {
        "ma_bn_an":                   patient_id,
        "current_date":               date.today().strftime("%d/%m/%Y"),
        "ho_ten":                     db_info.get("ho_ten", ""),
        "formatted_birthday":          db_info.get("formatted_birthday", ""),
        "age":                         db_info.get("age", ""),
        "ethnicity":                   db_info.get("ethnicity", ""),
        "dm_tinhcode":                 db_info.get("dm_tinhcode", ""),
        "isbn_ut":                     db_info.get("isbn_ut", ""),
        "cccd":                        db_info.get("cccd", ""),
        "medicalrecorddate_in":        db_info.get("medicalrecorddate_in", ""),
        "medicalrecorddate_out":       db_info.get("medicalrecorddate_out", ""),
        "chandoan_in":                 llm.get("chandoan_in") or db_info.get("chandoan_in", ""),
        "chandoan_in_icd10":           db_info.get("chandoan_in_icd10", ""),
        "chandoan_out_main":           llm.get("chandoan_out_main") or db_info.get("chandoan_out_main", ""),
        "chandoan_out_main_icd10":     llm.get("chandoan_out_main_icd10") or db_info.get("chandoan_out_main_icd10", ""),
        "lydodenkham":                 llm.get("lydodenkham") or db_info.get("lydodenkham", ""),
        "tom_tat_qua_trinh_dien_bien": llm.get("tom_tat_qua_trinh_dien_bien", ""),
        "tien_su_benh":                llm.get("tien_su_benh", ""),
        "dau_hieu_chinh":              llm.get("dau_hieu_chinh", ""),
        "tom_tat_ket_qua":             llm.get("tom_tat_ket_qua", ""),
        "departmentid":                db_info.get("departmentid", ""),
        "pttt":                        llm.get("pttt") or db_info.get("pttt", ""),
        "tinh_trang_ra_vien":          llm.get("tinh_trang_ra_vien", ""),
        "huongdieutri_out":            db_info.get("huongdieutri_out", "") or llm.get("huongdieutri_out", ""),
    }

    tpl = DocxTemplate(TEMPLATE_PATH)
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    return buf.getvalue()
