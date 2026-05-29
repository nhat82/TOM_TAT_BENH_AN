"""
Prompt versions for draft_summary and refine_summary.

Usage in summary_graph.py
--------------------------
    from app.graphs.prompts import PromptVersion, get_draft_messages, get_refine_messages

    _PROMPT_VERSION = PromptVersion.VI   # or PromptVersion.EN

    system, human = get_draft_messages(_PROMPT_VERSION, context, timeline_text)
    system, human = get_refine_messages(_PROMPT_VERSION, current_summary, instruction,
                                        history_section, context_section)

Both versions always produce Vietnamese output.
"""

from __future__ import annotations

import os
from enum import Enum

from langchain_core.messages import HumanMessage, SystemMessage


class PromptVersion(str, Enum):
    EN = "en"
    VI = "vi"


# ── draft system prompts ──────────────────────────────────────────────────────

_DRAFT_SYSTEM: dict[PromptVersion, str] = {
    PromptVersion.EN: (
        "You are a physician writing a medical record summary.\n"
        "Write a comprehensive, clear medical summary using specialized Vietnamese medical "
        "terminology. Do not use abbreviations or ICD-10 codes. If there's no information on a section, note that the information is not available.\n"
        "The summary must include:\n"
        "1. Patient information\n"
        "2. Reason for admission\n"
        "3. Medical history\n"
        "4. Primary and secondary diagnoses\n"
        "5. Treatment course and clinical progression\n"
        "6. Notable diagnostic and laboratory results\n"
        "7. Discharge status and follow-up treatment plan\n\n"
        "Write concisely, avoid repetition. Do not fabricate information outside the medical "
        "record. Always respond in Vietnamese."
    ),
    PromptVersion.VI: (
        "Bạn là bác sĩ viết tóm tắt bệnh án. "
        "Hãy viết văn bản bệnh án đầy đủ, rõ ràng, bằng tiếng Việt chuyên ngành y tế, "
        "không dùng từ viết tắt, không dùng mã ICD-10.\n"
        "Văn bản phải bao gồm:\n"
        "1. Thông tin bệnh nhân\n"
        "2. Lý do vào viện\n"
        "3. Tiền sử bệnh\n"
        "4. Chẩn đoán chính và kèm theo\n"
        "5. Quá trình điều trị và diễn biến lâm sàng\n"
        "6. Kết quả cận lâm sàng nổi bật\n"
        "7. Tình trạng ra viện và hướng điều trị tiếp theo\n\n"
        "Viết súc tích, tránh lặp lại. Không bịa đặt thông tin ngoài hồ sơ."
    ),
}

# ── draft human messages ──────────────────────────────────────────────────────

def _draft_human_en(timeline_text: str, context: str) -> str:
    return (
        f"Timeline of events:\n{timeline_text}\n\n"
        f"Detailed medical record:\n{context}"
    )


def _draft_human_vi(timeline_text: str, context: str) -> str:
    return (
        f"Timeline sự kiện:\n{timeline_text}\n\n"
        f"Hồ sơ chi tiết:\n{context}"
    )


_DRAFT_HUMAN_FN = {
    PromptVersion.EN: _draft_human_en,
    PromptVersion.VI: _draft_human_vi,
}

# ── refine system prompts ─────────────────────────────────────────────────────

_REFINE_SYSTEM: dict[PromptVersion, str] = {
    PromptVersion.EN: (
        "You are a physician editing a medical record summary.\n"
        "Apply the user's instruction to the current summary. Keep all unchanged sections "
        "intact. Return only the revised summary with no additional explanation.\n"
        "Always respond in Vietnamese."
    ),
    PromptVersion.VI: (
        "Bạn là bác sĩ chỉnh sửa tóm tắt bệnh án. "
        "Hãy chỉnh sửa tóm tắt bệnh án hiện tại theo đúng yêu cầu của người dùng. "
        "Giữ nguyên các phần không cần thay đổi. "
        "Chỉ trả về bản tóm tắt đã chỉnh sửa, không giải thích thêm."
    ),
}

# ── refine human messages ─────────────────────────────────────────────────────

def _refine_human_en(
    current_summary: str,
    instruction: str,
    history_section: str,
    context_section: str,
) -> str:
    return (
        f"Current summary:\n{current_summary}"
        f"{history_section}\n\n"
        f"New edit instruction: {instruction}"
        f"{context_section}"
    )


def _refine_human_vi(
    current_summary: str,
    instruction: str,
    history_section: str,
    context_section: str,
) -> str:
    return (
        f"Tóm tắt hiện tại:\n{current_summary}"
        f"{history_section}\n\n"
        f"Yêu cầu chỉnh sửa mới: {instruction}"
        f"{context_section}"
    )


_REFINE_HUMAN_FN = {
    PromptVersion.EN: _refine_human_en,
    PromptVersion.VI: _refine_human_vi,
}

# ── history / context section builders ───────────────────────────────────────

def build_history_section(history: list[dict], version: PromptVersion) -> str:
    if not history:
        return ""
    if version == PromptVersion.EN:
        lines = ["Previous edit history (oldest first):"]
        for i, entry in enumerate(history, 1):
            lines.append(f"  [{i}] Instruction: {entry.get('instruction', '')}")
    else:
        lines = ["Lịch sử chỉnh sửa trước đó (từ cũ đến mới):"]
        for i, entry in enumerate(history, 1):
            lines.append(f"  [{i}] Yêu cầu: {entry.get('instruction', '')}")
    return "\n" + "\n".join(lines)


def build_context_section(chunks: list[str], version: PromptVersion, top_n: int = 6) -> str:
    if not chunks:
        return ""
    if version == PromptVersion.EN:
        return "\n\nOriginal record (for reference if needed):\n" + "\n\n".join(chunks[:top_n])
    return (
        "\n\nHồ sơ gốc (để tham chiếu nếu cần):\n"
        + "\n\n".join(chunks[:top_n])
    )


# ── timeline system prompts ───────────────────────────────────────────────────

_TIMELINE_SYSTEM: dict[PromptVersion, str] = {
    PromptVersion.EN: (
        "You are a medical assistant. Extract a chronological list of events from the "
        "patient's record without using abbreviations. Return a JSON array where each "
        "element has the form:\n"
        '{"date": "YYYY-MM-DD or descriptive time", '
        '"event": "short event name", '
        '"detail": "brief detail"}\n'
        "Return only the raw JSON array, no additional explanation."
    ),
    PromptVersion.VI: (
        "Bạn là trợ lý y tế. Hãy trích xuất danh sách sự kiện theo thời gian "
        "từ hồ sơ bệnh nhân, không viết tắt. Trả về JSON array, mỗi phần tử có dạng:\n"
        '{"date": "YYYY-MM-DD hoặc mô tả thời điểm", '
        '"event": "tên sự kiện ngắn gọn", '
        '"detail": "chi tiết ngắn"}\n'
        "Chỉ trả về JSON array thuần túy, không giải thích thêm."
    ),
}

_TIMELINE_HUMAN: dict[PromptVersion, str] = {
    PromptVersion.EN: "Patient record:\n{context}",
    PromptVersion.VI: "Hồ sơ bệnh nhân:\n{context}",
}


# ── public API ────────────────────────────────────────────────────────────────

def get_timeline_messages(
    version: PromptVersion,
    context: str,
) -> tuple[SystemMessage, HumanMessage]:
    return (
        SystemMessage(content=_TIMELINE_SYSTEM[version]),
        HumanMessage(content=_TIMELINE_HUMAN[version].format(context=context)),
    )


def get_draft_messages(
    version: PromptVersion,
    context: str,
    timeline_text: str,
) -> tuple[SystemMessage, HumanMessage]:
    return (
        SystemMessage(content=_DRAFT_SYSTEM[version]),
        HumanMessage(content=_DRAFT_HUMAN_FN[version](timeline_text, context)),
    )


def get_refine_messages(
    version: PromptVersion,
    current_summary: str,
    instruction: str,
    history_section: str = "",
    context_section: str = "",
) -> tuple[SystemMessage, HumanMessage]:
    return (
        SystemMessage(content=_REFINE_SYSTEM[version]),
        HumanMessage(content=_REFINE_HUMAN_FN[version](
            current_summary, instruction, history_section, context_section
        )),
    )


# ── default version (override via SUMMARY_PROMPT_VERSION env var) ─────────────

DEFAULT_VERSION = PromptVersion(os.getenv("SUMMARY_PROMPT_VERSION", PromptVersion.VI))
