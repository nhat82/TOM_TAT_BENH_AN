"""
Build a formatted DOCX from a Vietnamese medical summary string.

Section detection: lines matching "^\\d+\\.\\s" or "^\\*\\*\\d+\\.\\s" are
treated as numbered headings; everything else becomes body paragraph text.
"""

from __future__ import annotations

import io
import re
from datetime import date

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


_SECTION_RE = re.compile(r"^\*{0,2}(\d+)\.\s+(.+?)\*{0,2}$")

# ── helpers ───────────────────────────────────────────────────────────────────

def _set_cell_bg(cell, hex_color: str) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _add_horizontal_rule(doc: Document) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pb = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "BDBDBD")
    pb.append(bottom)
    pPr.append(pb)


# ── parser ────────────────────────────────────────────────────────────────────

def _parse_summary(text: str) -> list[tuple[str, str]]:
    """
    Return a list of (kind, content) tuples:
      ("heading", "1. Section title")
      ("body",    "Paragraph text …")
    """
    blocks: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = _SECTION_RE.match(line)
        if m:
            blocks.append(("heading", f"{m.group(1)}. {m.group(2)}"))
        else:
            blocks.append(("body", line))
    return blocks


# ── public API ────────────────────────────────────────────────────────────────

def build_docx(patient_id: str, summary: str) -> bytes:
    """
    Render *summary* as a formatted DOCX and return raw bytes.
    """
    doc = Document()

    # ── page margins ──────────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin    = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin   = Inches(1.2)
        section.right_margin  = Inches(1.2)

    # ── title block ───────────────────────────────────────────────────────────
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(4)
    run = title.add_run("TÓM TẮT BỆNH ÁN")
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(0x1A, 0x73, 0xE8)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.space_after = Pt(2)
    mr = meta.add_run(f"Mã bệnh nhân: {patient_id}    |    Ngày xuất: {date.today().strftime('%d/%m/%Y')}")
    mr.font.size = Pt(10)
    mr.font.color.rgb = RGBColor(0x75, 0x75, 0x75)

    _add_horizontal_rule(doc)
    doc.add_paragraph()  # spacer

    # ── body ──────────────────────────────────────────────────────────────────
    for kind, content in _parse_summary(summary):
        if kind == "heading":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after  = Pt(4)
            run = p.add_run(content)
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0x1A, 0x73, 0xE8)
        else:
            p = doc.add_paragraph(content)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after  = Pt(4)
            for run in p.runs:
                run.font.size = Pt(11)

    # ── footer ────────────────────────────────────────────────────────────────
    _add_horizontal_rule(doc)
    footer_p = doc.add_paragraph()
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = footer_p.add_run("Tài liệu được tạo tự động")
    fr.font.size = Pt(8)
    fr.font.color.rgb = RGBColor(0xBD, 0xBD, 0xBD)
    fr.italic = True

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
