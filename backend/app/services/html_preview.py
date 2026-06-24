"""
Render patient summary as a self-contained HTML document replicating the
official Mẫu số 03 — Bản Tóm Tắt Hồ Sơ Bệnh Án layout.
"""
from __future__ import annotations

from datetime import date
from html import escape

from app.services.docx_export import _parse_summary_json


def _v(val: str) -> str:
    return escape(str(val)) if val else "&nbsp;"


def build_preview_html(patient_id: str, summary: str, patient_info: dict | None = None) -> str:
    today = date.today().strftime("%d/%m/%Y")
    pid = escape(patient_id)
    info = patient_info or {}
    llm = _parse_summary_json(summary)

    chandoan_in_icd10  = info.get("chandoan_in_icd10", "")
    chandoan_out_icd10 = llm.get("chandoan_out_main_icd10") or info.get("chandoan_out_main_icd10", "")
    chandoan_in        = llm.get("chandoan_in")             or info.get("chandoan_in", "")
    chandoan_out_main  = llm.get("chandoan_out_main")       or info.get("chandoan_out_main", "")
    lydodenkham        = llm.get("lydodenkham")             or info.get("lydodenkham", "")
    pttt               = llm.get("pttt")                    or info.get("pttt", "")
    huongdieutri_out   = info.get("huongdieutri_out", "")   or llm.get("huongdieutri_out", "")

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
  body{{font-family:"Times New Roman",Times,serif;font-size:13px;color:#111;
       margin:0;padding:30px 50px;background:#fff;max-width:800px;margin:0 auto}}
  .hdr{{display:grid;grid-template-columns:1fr 1.6fr 1fr;gap:8px;margin-bottom:4px;font-size:12px}}
  .hdr-c{{text-align:center}}
  .hdr-r{{text-align:right}}
  .pg-title{{text-align:center;font-size:15px;font-weight:bold;text-transform:uppercase;margin:18px 0 14px}}
  .sh{{font-weight:bold;font-size:13px;text-transform:uppercase;margin:14px 0 6px}}
  .fr{{margin:5px 0;line-height:1.6}}
  .ind{{margin-left:14px}}
  .sig{{text-align:right;margin-top:24px;font-size:12px;font-style:italic}}
  .sig b{{display:block;font-style:normal}}
</style>
</head>
<body>
<div class="hdr">
  <div><b>CƠ QUAN CHỦ QUẢN</b><br><b>TÊN CƠ SỞ KCB</b><br>------</div>
  <div class="hdr-c">
    <b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br>
    Độc lập - Tự do - Hạnh phúc<br>--------------
  </div>
  <div class="hdr-r">Số hồ sơ/Số BA<br><b>{pid}</b></div>
</div>
<div style="font-size:12px">Số: &nbsp;/….</div>

<div class="pg-title">Mẫu số 03. Bản Tóm Tắt Hồ Sơ Bệnh Án</div>
<div class="pg-title" style="font-size:16px;margin-top:-8px">BẢN TÓM TẮT HỒ SƠ BỆNH ÁN</div>

<div class="sh">I. HÀNH CHÍNH</div>
<div class="fr">Họ và tên (In hoa): <b>{_v(info.get("ho_ten",""))}</b> &nbsp;&nbsp; Ngày sinh: {_v(info.get("formatted_birthday",""))}</div>
<div class="fr">Tuổi: {_v(info.get("age",""))} &nbsp; Giới tính: □ Nam &nbsp; □ Nữ</div>
<div class="fr">Dân tộc: {_v(info.get("ethnicity",""))}</div>
<div class="fr">Địa chỉ: {_v(info.get("dm_tinhcode",""))}</div>
<div class="fr">Số thẻ BHYT: {_v(info.get("isbn_ut",""))}</div>
<div class="fr">Số Căn cước/Hộ chiếu/Mã định danh cá nhân: {_v(info.get("cccd",""))}</div>
<div class="fr">Vào viện ngày {_v(info.get("medicalrecorddate_in",""))} &nbsp; Ra viện ngày {_v(info.get("medicalrecorddate_out",""))}</div>

<div class="sh">II. CHẨN ĐOÁN <span style="font-weight:normal;font-size:12px">(Tên bệnh và mã ICD đính kèm):</span></div>
<div class="fr">Chẩn đoán vào viện: {_v(chandoan_in)} - {_v(chandoan_in_icd10)}</div>
<div class="fr">Chẩn đoán ra viện: {_v(chandoan_out_main)} - {_v(chandoan_out_icd10)}</div>

<div class="sh">III. TÓM TẮT QUÁ TRÌNH ĐIỀU TRỊ</div>
<div class="fr"><u>Lý do vào viện:</u> {_v(lydodenkham)}</div>
<div class="fr" style="margin-top:8px"><u>Tóm tắt quá trình bệnh lý và diễn biến lâm sàng (Đặc điểm khởi phát, các triệu chứng lâm sàng, diễn biến bệnh...):</u> {_v(llm.get("tom_tat_qua_trinh_dien_bien",""))}</div>
<div class="fr" style="margin-top:8px"><u>Tiền sử bệnh:</u> {_v(llm.get("tien_su_benh",""))}</div>
<div class="fr" style="margin-top:8px"><u>Những dấu hiệu lâm sàng chính được ghi nhận (có giá trị chẩn đoán trong quá trình điều trị):</u> {_v(llm.get("dau_hieu_chinh",""))}</div>
<div class="fr" style="margin-top:8px"><u>Tóm tắt kết quả xét nghiệm, cận lâm sàng có giá trị chẩn đoán:</u> {_v(llm.get("tom_tat_ket_qua",""))}</div>
<div class="fr" style="margin-top:8px"><u>Phương pháp điều trị (tương ứng với chẩn đoán):</u></div>
<div class="fr"><u>Nội khoa:</u> □ Không &nbsp; □ Có, ghi rõ: {_v(info.get("departmentid",""))}</div>
<div class="fr"><u>Phẫu thuật, thủ thuật:</u> □ Không &nbsp; □ Có, ghi rõ phương pháp: {_v(pttt)}</div>
<div class="fr" style="margin-top:8px"><u>Tình trạng ra viện:</u></div>
<div class="fr">□ Khỏi &nbsp; □ Đỡ &nbsp; □ Không thay đổi &nbsp; □ Nặng hơn &nbsp; □ Tử vong &nbsp; □ Tiên lượng nặng xin về</div>
<div class="fr">□ Chưa xác định</div>
<div class="fr ind" style="font-style:italic">{_v(llm.get("tinh_trang_ra_vien",""))}</div>
<div class="fr" style="margin-top:8px"><u>Hướng điều trị và các chế độ tiếp theo:</u> {_v(huongdieutri_out)}</div>

<div class="sig">
  {today}<br><b>Đại diện đơn vị</b><br>(Ký, đóng dấu)
</div>
</body>
</html>"""
