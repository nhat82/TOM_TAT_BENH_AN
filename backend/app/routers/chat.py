"""
POST /api/chat
--------------
Request
  { "id_benh_nhan": str, "query": str, "chat_history": [{role, content}] }

Response  (SSE, text/event-stream)
  data: {"type": "token",  "content": "…"}
  data: {"type": "done",   "sources": ["record-id", …]}
  data: {"type": "error",  "detail": "…"}

Each turn is checkpointed by MemorySaver (thread_id = patient_id).
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.graphs.chat_graph import chat_graph

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


# ── request schema ─────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    id_benh_nhan: str
    query: str
    chat_history: list[ChatMessage] = []


# ── SSE helpers ────────────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ── endpoint ───────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    input_state = {
        "patient_id": body.id_benh_nhan,
        "question":   body.query,
        "history":    [m.model_dump() for m in body.chat_history],
    }
    config = {"configurable": {"thread_id": body.id_benh_nhan}}

    async def generate():
        try:
            sources: list[str] = []

            async for event in chat_graph.astream_events(
                input_state, config=config, version="v2"
            ):
                kind = event["event"]
                name = event.get("name", "")

                if kind == "on_chat_model_stream":
                    token: str = event["data"]["chunk"].content
                    if token:
                        yield _sse({"type": "token", "content": token})

                elif kind == "on_chain_end" and name == "LangGraph":
                    output = event["data"].get("output") or {}
                    sources = output.get("sources", [])

            yield _sse({"type": "done", "sources": sources})

        except ValueError as exc:
            log.warning("chat error (patient not found): %s", exc)
            yield _sse({"type": "error", "detail": str(exc)})
        except Exception as exc:
            log.exception("chat generation failed")
            yield _sse({"type": "error", "detail": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream")
