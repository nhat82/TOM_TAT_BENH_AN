"""
Render a patient summary as a self-contained HTML document for browser preview.
Mirrors the visual layout of the DOCX export from docx_export.py.
"""
from __future__ import annotations

import re
from datetime import date
from html import escape

_SECTION_RE = re.compile(r"^\*{0,2}(\d+)\.\s+(.+?)\*{0,2}$")

_PATIENT_LABELS = [
    ("patient_name",   "Họ tên"),
    ("birthday",       "Năm sinh"),
    ("age",            "Tuổi"),
    ("gender",         "Giới tính"),
    ("ethnicity",      "Dân tộc"),
    ("address",        "Địa chỉ"),
    ("id_number",      "Số CMND/CCCD"),
    ("admission_date", "Ngày nhập viện"),
    ("discharge_date", "Ngày xuất viện"),
]


def _parse_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _SECTION_RE.match(line)
        if m:
            blocks.append(("heading", f"{m.group(1)}. {m.group(2)}"))
        else:
            blocks.append(("body", line))
    return blocks


def build_preview_html(patient_id: str, summary: str, patient_info: dict | None = None) -> str:
    today = date.today().strftime("%d/%m/%Y")
    pid = escape(patient_id)

    demo_rows = ""
    if patient_info:
        for key, label in _PATIENT_LABELS:
            val = patient_info.get(key, "")
            if val:
                demo_rows += (
                    f'<tr><td class="lc">{escape(label)}</td>'
                    f'<td class="vc">{escape(str(val))}</td></tr>'
                )

    demo_table = (
        f'<table class="dt"><tbody>{demo_rows}</tbody></table>'
        if demo_rows else ""
    )

    body_html = ""
    for kind, content in _parse_blocks(summary):
        c = escape(content)
        if kind == "heading":
            body_html += f'<p class="sh">{c}</p>\n'
        else:
            body_html += f'<p class="bt">{c}</p>\n'

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<style>
  body{{font-family:"Times New Roman",Times,serif;font-size:13px;color:#212121;
       margin:0;padding:40px 60px;background:#fff}}
  .title{{text-align:center;font-size:20px;font-weight:bold;color:#1a73e8;
          letter-spacing:.05em;margin-bottom:4px}}
  .meta{{text-align:center;font-size:11px;color:#757575;margin-bottom:12px}}
  hr{{border:none;border-top:1px solid #bdbdbd;margin:8px 0 16px}}
  .dt{{width:100%;border-collapse:collapse;margin-bottom:16px;font-size:12px}}
  .lc{{background:#eaf2ff;font-weight:bold;padding:5px 10px;
       width:160px;border:1px solid #ccc}}
  .vc{{padding:5px 10px;border:1px solid #ccc}}
  .sh{{font-weight:bold;color:#1a73e8;font-size:13px;margin:16px 0 4px}}
  .bt{{margin:2px 0 4px;line-height:1.65}}
  .footer{{text-align:center;font-size:10px;color:#bdbdbd;font-style:italic;margin-top:16px}}
</style>
</head>
<body>
  <p class="title">TÓM TẮT BỆNH ÁN</p>
  <p class="meta">Mã bệnh nhân: {pid}&nbsp;&nbsp;|&nbsp;&nbsp;Ngày xuất: {today}</p>
  <hr>
  {demo_table}
  {body_html}
  <hr>
  <p class="footer">Tài liệu được tạo tự động</p>
</body>
</html>"""
