"""
RAG summary graph for a single patient
=======================================

Nodes
-----
retrieve        – pull the patient's document from ChromaDB, split into
                  section chunks, rerank against the summary task so the
                  LLM receives the most clinically relevant context first.
build_timeline  – LLM extracts a chronological event list from the chunks.
draft_summary   – LLM writes a comprehensive Vietnamese medical summary
                  using chunks + timeline.

State
-----
SummaryState is the single shared dict that flows through every node.
"""

from __future__ import annotations

import json
import logging
import os
import requests
import base64
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.graphs.prompts import (
    DEFAULT_VERSION,
    PromptVersion,
    build_context_section,
    build_history_section,
    get_draft_messages,
    get_refine_messages,
    get_timeline_messages,
)
from app.services.chroma import get_collection
from app.services.llm import get_summary_llm

# Change to PromptVersion.EN to use the English-instruction prompts.
# Override at runtime with env var SUMMARY_PROMPT_VERSION=en|vi.
PROMPT_VERSION: PromptVersion = DEFAULT_VERSION.EN

log = logging.getLogger(__name__)

# ── state ─────────────────────────────────────────────────────────────────────

class SummaryState(TypedDict):
    patient_id: str
    chunks: list[str]       # section chunks from ChromaDB, reranked
    draft: str              # final Vietnamese medical summary
    timeline: list[dict]    # [{date, event, detail}, …]


# ── helpers ───────────────────────────────────────────────────────────────────

def _split_into_chunks(document: str) -> list[str]:
    """
    Split a labelled document ("\\n[LABEL] text\\n[LABEL] text…") into
    individual section strings so the reranker can score them separately.
    """
    chunks: list[str] = []
    current: list[str] = []
    for line in document.splitlines():
        if line.startswith("[") and "]" in line and current:
            chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c]


def _rerank_chunks(query: str, chunks: list[str], top_n: int = 12) -> list[str]:
    return chunks[:top_n]
    

def save_mermaid_to_png(mermaid_str, output_filename):
    # Encode the string for the URL
    ascii_msg = mermaid_str.encode('ascii')
    base64_bytes = base64.b64encode(ascii_msg)
    base64_string = base64_bytes.decode('ascii')
    
    url = f"https://mermaid.ink/img/{base64_string}"
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(output_filename, "wb") as f:
            f.write(response.content)
        print(f"Success! Saved to {output_filename}")
    else:
        print(f"Failed to fetch image. Status: {response.status_code}")


# ── nodes ─────────────────────────────────────────────────────────────────────

def retrieve(state: SummaryState) -> dict:
    """
    Fetch the patient's stored document from ChromaDB, split it into section
    chunks, then rerank so the LLM receives the most relevant context.

    Raises ValueError when the patient ID is not found (converted to 404
    by the router).
    """
    pid = state["patient_id"]
    collection = get_collection()

    result = collection.get(
        ids=[pid],
        include=["documents", "metadatas"],
    )

    if not result["documents"] or not result["documents"][0]:
        raise ValueError(f"Patient '{pid}' not found in ChromaDB. Run ingest first.")

    document = result["documents"][0]
    raw_chunks = _split_into_chunks(document)

    rerank_query = "tóm tắt bệnh án toàn diện: chẩn đoán, quá trình điều trị, kết quả"
    ranked_chunks = _rerank_chunks(rerank_query, raw_chunks)

    log.info("retrieve: %d section(s) → top %d after rerank", len(raw_chunks), len(ranked_chunks))
    return {"chunks": ranked_chunks}


def build_timeline(state: SummaryState) -> dict:
    """
    Ask the LLM to extract a structured chronological event list from the
    patient's chunks.  Returns timeline as list[dict].
    """
    context = "\n\n".join(state["chunks"])
    llm = get_summary_llm()

    system, human = get_timeline_messages(PROMPT_VERSION, context)

    response = llm.invoke([system, human])
    content = response.content
    if isinstance(content, list):
        # Join all text pieces together, ignoring non-text blocks if they exist
        raw = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content]).strip()
    else:
        # If it's already a string, strip it normally
        raw = content.strip()
    

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        timeline = json.loads(raw)
        if not isinstance(timeline, list):
            timeline = []
    except json.JSONDecodeError:
        log.warning("build_timeline: could not parse JSON — returning empty timeline.")
        timeline = []

    log.info("build_timeline: %d event(s) extracted.", len(timeline))
    return {"timeline": timeline}


def draft_summary(state: SummaryState) -> dict:
    """
    Write a comprehensive Vietnamese medical summary using the reranked
    chunks plus the structured timeline.
    """
    context = "\n\n".join(state["chunks"])
    timeline_text = json.dumps(state["timeline"], ensure_ascii=False, indent=2)
    llm = get_summary_llm()

    system, human = get_draft_messages(PROMPT_VERSION, context, timeline_text)

    response = llm.invoke([system, human])
    
    content = response.content
    if isinstance(content, list):
        # Join all text pieces together, ignoring non-text blocks if they exist
        draft = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content]).strip()
    else:
        # If it's already a string, strip it normally
        draft = content.strip()
    
    log.info("draft_summary: %d character(s) generated.", len(draft))
    return {"draft": draft}


# ── refine ────────────────────────────────────────────────────────────────────

async def refine_summary(
    current_summary: str,
    instruction: str,
    chunks: list[str] | None = None,
    history: list[dict] | None = None,
) -> str:
    """
    Refine an existing summary based on a user instruction.

    history: list of {instruction, result_summary} from prior refinement turns,
             oldest first. Lets the LLM understand what has already been done.
    chunks:  original document sections for grounding (optional).
    """
    llm = get_summary_llm()

    history_section = build_history_section(history or [], PROMPT_VERSION)
    context_section = build_context_section(chunks or [], PROMPT_VERSION)
    system, human = get_refine_messages(
        PROMPT_VERSION, current_summary, instruction, history_section, context_section
    )

    response = await llm.ainvoke([system, human])
    content = response.content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    return content.strip()


# ── graph factory ─────────────────────────────────────────────────────────────

def build_graph():
    """
    Compile and return the summary StateGraph.

    Edges: START → retrieve → build_timeline → draft_summary → END
    """
    g = StateGraph(SummaryState)

    g.add_node("retrieve",       retrieve)
    g.add_node("build_timeline", build_timeline)
    g.add_node("draft_summary",  draft_summary)

    g.add_edge(START,            "retrieve")
    g.add_edge("retrieve",       "build_timeline")
    g.add_edge("build_timeline", "draft_summary")
    g.add_edge("draft_summary",  END)

    return g.compile()


# Compiled graph — imported by the router
summary_graph = build_graph()

mermaid_text = summary_graph.get_graph().draw_mermaid()
save_mermaid_to_png(mermaid_text, "summary_graph.png")