import json
from unittest.mock import MagicMock, patch

import pytest


def _mock_row(**kwargs):
    m = MagicMock()
    m.get = lambda key, default="": kwargs.get(key, default)
    return m


def _mock_db_with_row(row):
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = row
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_db = MagicMock()
    mock_db._engine.connect.return_value.__enter__ = lambda s: mock_conn
    mock_db._engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return mock_db


def test_fetch_patient_info_maps_fields():
    from app.services.docx_export import fetch_patient_info

    row = _mock_row(
        ho_ten="Nguyễn Văn A",
        birthdayyear="1972",
        dm_gioitinhid="1",
        dm_dantoc="Kinh",
        dm_tinhcode="Hà Nội",
        isbn_ut="BH123456",
        cccd="012345678901",
        medicalrecorddate_in="2026-03-02 09:19:23",
        medicalrecorddate_out="2026-03-05 08:19:57",
        chandoan_in="Ung thư đại tràng",
        chandoan_in_icd10="",
        chandoan_out_main="Ung thư đại tràng",
        chandoan_out_main_icd10="",
        lydodenkham="Đau bụng",
        departmentid="Khoa ngoại",
        pttt="",
        huongdieutri_out="Tiếp tục điều trị",
    )
    with patch("app.services.docx_export.db", _mock_db_with_row(row)):
        result = fetch_patient_info("BN0001")

    assert result["ho_ten"] == "Nguyễn Văn A"
    assert result["gender"] == "Nam"
    assert result["ethnicity"] == "Kinh"
    assert result["medicalrecorddate_in"] == "02/03/2026"
    assert result["medicalrecorddate_out"] == "05/03/2026"
    assert result["chandoan_in"] == "Ung thư đại tràng"
    assert result["huongdieutri_out"] == "Tiếp tục điều trị"
    assert result["age"] != ""  # calculated from birthdayyear
    # legacy keys still present
    assert result["patient_name"] == "Nguyễn Văn A"
    assert result["admission_date"] == "02/03/2026"


def test_fetch_patient_info_returns_empty_on_missing_patient():
    from app.services.docx_export import fetch_patient_info

    with patch("app.services.docx_export.db", _mock_db_with_row(None)):
        result = fetch_patient_info("UNKNOWN")

    assert result == {}


def test_parse_summary_json_valid():
    from app.services.docx_export import _parse_summary_json

    data = {
        "chandoan_in_icd10": "C18.7",
        "chandoan_out_main_icd10": "C18.7",
        "tom_tat_qua_trinh_dien_bien": "Bệnh nhân nhập viện",
        "tien_su_benh": "Không có",
        "dau_hieu_chinh": "Đau hạ sườn",
        "tom_tat_ket_qua": "CEA tăng",
        "pttt": "",
        "tinh_trang_ra_vien": "Đỡ",
        "huongdieutri_out": "Tái khám 2 tuần",
    }
    result = _parse_summary_json(json.dumps(data))
    assert result["chandoan_in_icd10"] == "C18.7"
    assert result["tinh_trang_ra_vien"] == "Đỡ"
    assert result["tom_tat_qua_trinh_dien_bien"] == "Bệnh nhân nhập viện"


def test_parse_summary_json_invalid_returns_empty_strings():
    from app.services.docx_export import _parse_summary_json

    result = _parse_summary_json("This is not JSON at all")
    assert result["chandoan_in_icd10"] == ""
    assert result["tom_tat_qua_trinh_dien_bien"] == ""
    assert result["tinh_trang_ra_vien"] == ""


def test_build_preview_html_mau_so_03_sections():
    from app.services.html_preview import build_preview_html

    patient_info = {
        "ho_ten": "Nguyễn Văn A",
        "formatted_birthday": "01/01/1972",
        "age": "54",
        "gender": "Nam",
        "ethnicity": "Kinh",
        "dm_tinhcode": "Hà Nội",
        "isbn_ut": "BH123",
        "cccd": "012345678901",
        "medicalrecorddate_in": "02/03/2026",
        "medicalrecorddate_out": "05/03/2026",
        "chandoan_in": "Ung thư đại tràng",
        "chandoan_in_icd10": "",
        "chandoan_out_main": "Ung thư đại tràng",
        "chandoan_out_main_icd10": "",
        "lydodenkham": "Đau bụng",
        "departmentid": "Khoa ngoại",
        "pttt": "",
        "huongdieutri_out": "Tái khám",
    }
    summary_json = json.dumps({
        "chandoan_in_icd10": "C18.7",
        "chandoan_out_main_icd10": "C18.7",
        "tom_tat_qua_trinh_dien_bien": "Bệnh diễn biến phức tạp",
        "tien_su_benh": "Không có",
        "dau_hieu_chinh": "Đau bụng dữ dội",
        "tom_tat_ket_qua": "CEA tăng",
        "pttt": "",
        "tinh_trang_ra_vien": "Đỡ",
        "huongdieutri_out": "Tái khám 2 tuần",
    })

    html = build_preview_html("BN0001", summary_json, patient_info)

    assert "BẢN TÓM TẮT HỒ SƠ BỆNH ÁN" in html
    assert "HÀNH CHÍNH" in html
    assert "CHẨN ĐOÁN" in html
    assert "QUÁ TRÌNH ĐIỀU TRỊ" in html
    assert "Nguyễn Văn A" in html
    assert "Ung thư đại tràng" in html
    assert "C18.7" in html
    assert "Bệnh diễn biến phức tạp" in html
    assert "Đỡ" in html
    assert "BN0001" in html
    assert "Đại diện đơn vị" in html
