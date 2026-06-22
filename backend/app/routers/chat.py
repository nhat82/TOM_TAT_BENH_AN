from __future__ import annotations
"""
POST /api/chat
--------------
Request
  { "patient_id": str, "query": str, "chat_history": [{role, content}] }

Response  (SSE, text/event-stream)
  data: {"type": "token",  "content": "…"}
  data: {"type": "done"}
  data: {"type": "error",  "detail": "…"}

Each conversation thread is checkpointed by MemorySaver (thread_id = patient_id).
"""



import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.agent_package.agents.chatbot_agent import chatbot_agent

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


# ── request / response schemas ─────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    patient_id: str
    query: str
    chat_history: list[ChatMessage] = []


# ── SSE helper ─────────────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ── endpoint ───────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    history = [m.model_dump() for m in body.chat_history]
    input_state = {
        "patient_id": body.patient_id,
        "messages": history + [{"role": "user", "content": body.query}],
    }
    config = {"configurable": {"thread_id": body.patient_id}}

    async def generate():
        try:
            async for event in chatbot_agent.astream_events(input_state, config=config, version="v2"):
                if event["event"] == "on_chat_model_stream":
                    raw = event["data"]["chunk"].content
                    if isinstance(raw, list):
                        token = "".join(
                            p.get("text", "") if isinstance(p, dict) else str(p)
                            for p in raw
                        )
                    else:
                        token = raw
                    if token:
                        yield _sse({"type": "token", "content": token})

            yield _sse({"type": "done"})

        except ValueError as exc:
            log.warning("chat error: %s", exc)
            yield _sse({"type": "error", "detail": str(exc)})
        except Exception as exc:
            log.exception("chat generation failed")
            yield _sse({"type": "error", "detail": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream")
