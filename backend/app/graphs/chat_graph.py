"""
RAG chat graph for patient Q&A
================================

Nodes
-----
embed_question  – encode the user's question with the Vietnamese bi-encoder
retrieve_chunks – fetch the patient's document, split into sections,
                  rank sections by cosine similarity to the question
generate_answer – call the LLM with context + chat history (streamed via
                  astream_events in the router; result stored in state)

State
-----
ChatState is the single shared dict flowing through every node.
answer_stream is a conceptual field — actual streaming is emitted by
LangGraph's astream_events mechanism so MemorySaver can serialize state.

Memory
------
MemorySaver checkpoints every node's output, keyed by thread_id
(patient_id passed in config).  The server retains the full run history
for auditing even though the client sends chat_history on every request.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, TypedDict

import numpy as np
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.services.chroma import get_collection
from app.services.llm import get_llm

log = logging.getLogger(__name__)


# ── state ─────────────────────────────────────────────────────────────────────

class ChatState(TypedDict):
    patient_id: str
    question: str
    history: list[dict]       # [{"role": "user"|"assistant", "content": "…"}]
    embedding: list[float]
    chunks: list[str]
    sources: list[str]
    answer_stream: AsyncGenerator  # never set in nodes; streaming via astream_events
    answer: str                    # stored in checkpoint after generation


# ── embedder ──────────────────────────────────────────────────────────────────

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        log.info("Loading vietnamese-bi-encoder…")
        _embedder = SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder")
    return _embedder


def _embed(texts: list[str]) -> list[list[float]]:
    return _get_embedder().encode(texts, normalize_embeddings=True, batch_size=32).tolist()


# ── chunk helpers ─────────────────────────────────────────────────────────────

def _split_into_chunks(document: str) -> list[str]:
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


def _rank_chunks(q_emb: list[float], chunks: list[str], top_n: int = 6) -> list[str]:
    if not chunks:
        return []
    chunk_embs = _embed(chunks)
    q = np.array(q_emb)
    # embeddings are already L2-normalised — dot product == cosine similarity
    scores = [float(np.dot(q, np.array(e))) for e in chunk_embs]
    ranked = sorted(zip(scores, chunks), reverse=True)
    return [c for _, c in ranked[:top_n]]


# ── nodes ─────────────────────────────────────────────────────────────────────

def embed_question(state: ChatState) -> dict:
    return {"embedding": _embed([state["question"]])[0]}


def retrieve_chunks(state: ChatState) -> dict:
    pid = state["patient_id"]
    collection = get_collection()

    result = collection.get(ids=[pid], include=["documents"])
    if not result["documents"] or not result["documents"][0]:
        raise ValueError(f"Patient '{pid}' not found in ChromaDB. Run ingest first.")

    document = result["documents"][0]
    all_chunks = _split_into_chunks(document)
    top_chunks = _rank_chunks(state["embedding"], all_chunks)

    log.info(
        "retrieve_chunks: patient='%s'  %d sections → top %d",
        pid, len(all_chunks), len(top_chunks),
    )
    return {"chunks": top_chunks, "sources": [pid]}


async def generate_answer(state: ChatState) -> dict:
    context = "\n\n".join(state["chunks"])
    llm = get_llm()

    messages = [
        SystemMessage(content=(
            "Bạn là trợ lý y tế chuyên trả lời câu hỏi về hồ sơ bệnh nhân. "
            "Chỉ trả lời dựa trên thông tin trong hồ sơ được cung cấp. "
            "Nếu thông tin không có trong hồ sơ, hãy nói rõ điều đó. "
            "Trả lời bằng tiếng Việt, súc tích và chính xác.\n\n"
            f"Hồ sơ bệnh nhân:\n{context}"
        ))
    ]

    for turn in state.get("history", []):
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=state["question"]))

    response = await llm.ainvoke(messages)
    answer = response.content.strip()
    log.info("generate_answer: patient='%s'  %d chars", state["patient_id"], len(answer))
    return {"answer": answer}


# ── graph factory ─────────────────────────────────────────────────────────────

_memory = MemorySaver()


def build_graph():
    g = StateGraph(ChatState)

    g.add_node("embed_question",  embed_question)
    g.add_node("retrieve_chunks", retrieve_chunks)
    g.add_node("generate_answer", generate_answer)

    g.add_edge(START,             "embed_question")
    g.add_edge("embed_question",  "retrieve_chunks")
    g.add_edge("retrieve_chunks", "generate_answer")
    g.add_edge("generate_answer", END)

    return g.compile(checkpointer=_memory)


chat_graph = build_graph()
