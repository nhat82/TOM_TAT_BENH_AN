"""
Build a formatted DOCX from a Vietnamese medical summary using the official
Mẫu số 03 — Bản Tóm Tắt Hồ Sơ Bệnh Án docxtpl template.
"""
from __future__ import annotations

import io
import json
import logging
import os
from datetime import date, datetime

from docxtpl import DocxTemplate
from sqlalchemy import text

from app.services.database import db

log = logging.getLogger(__name__)

TEMPLATE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "mau_so_03.docx")
)

_NULL_VALUES = {"nan", "none", "", "0", "0.0", "0001-01-01 00:00:00"}

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


def _clean(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in _NULL_VALUES else s


def _fmt_date(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in _NULL_VALUES:
        return ""
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return s


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
    """Query medical_records for all Mẫu số 03 template fields."""
    try:
        with db._engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM medical_records WHERE ma_bn_an = :pid LIMIT 1"),
                {"pid": pid},
            )
            row = result.mappings().first()
    except Exception:
        log.warning("Could not fetch patient info for %s", pid)
        return {}

    if not row:
        return {}

    gender_map = {"1": "Nam", "2": "Nữ"}
    birth_year = _clean(row.get("birthdayyear", ""))
    birthday_full = _clean(row.get("birthday", ""))
    formatted_birthday = _fmt_date(birthday_full) if birthday_full else birth_year

    age = ""
    if birth_year:
        try:
            age = str(date.today().year - int(birth_year))
        except ValueError:
            pass

    gender_raw = _clean(row.get("dm_gioitinhid", ""))
    gender = gender_map.get(gender_raw, gender_raw)

    return {
        "ho_ten":                 _clean(row.get("ho_ten", ""))                  or "",
        "formatted_birthday":      formatted_birthday                              or "",
        "age":                     age,
        "gender":                  gender,
        "ethnicity":               _clean(row.get("dm_dantoc", ""))               or "",
        "dm_tinhcode":             _clean(row.get("dm_tinhcode", ""))             or "",
        "isbn_ut":                 _clean(row.get("isbn_ut", ""))                 or "",
        "cccd":                    _clean(row.get("cccd", ""))                    or "",
        "medicalrecorddate_in":    _fmt_date(row.get("medicalrecorddate_in"))     or "",
        "medicalrecorddate_out":   _fmt_date(row.get("medicalrecorddate_out"))    or "",
        "chandoan_in":             _clean(row.get("chandoan_in", ""))             or "",
        "chandoan_in_icd10":       _clean(row.get("chandoan_in_icd10", ""))       or "",
        "chandoan_out_main":       _clean(row.get("chandoan_out_main", ""))       or "",
        "chandoan_out_main_icd10": _clean(row.get("chandoan_out_main_icd10", "")) or "",
        "lydodenkham":             _clean(row.get("lydodenkham", ""))             or "",
        "departmentid":            _clean(row.get("departmentid", ""))            or "",
        "pttt":                    _clean(row.get("pttt", ""))                    or "",
        "huongdieutri_out":        _clean(row.get("huongdieutri_out", ""))        or "",
        # Legacy keys used by existing callers
        "patient_name":            _clean(row.get("ho_ten", ""))                  or "",
        "birthday":                birth_year                                      or "",
        "id_number":               _clean(row.get("cccd", ""))                    or "",
        "province":                _clean(row.get("dm_tinhcode", ""))             or "",
        "admission_date":          _fmt_date(row.get("medicalrecorddate_in"))     or "",
        "discharge_date":          _fmt_date(row.get("medicalrecorddate_out"))    or "",
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
