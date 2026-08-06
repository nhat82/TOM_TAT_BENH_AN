import json
import logging
from datetime import datetime

import opik
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from app.core.security import pii_masker
from app.modules.patient_chat.services.agent_chat import chat_streaming

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


# ── request / response schemas ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    patient_id: str
    query: str


# ── SSE helper ─────────────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ── endpoint ───────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    message_key = f"{body.patient_id}:{datetime.now().isoformat()}"

    @opik.track(name="chat_generate")
    async def generate(message_key: str, chat_request: ChatRequest):
        tool_calls = 0
        try:
            async for event in chat_streaming(
                patient_id=chat_request.patient_id,
                query=chat_request.query,
                message_key=message_key,
            ):
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
                        exposed = pii_masker.unmask(message_key, token)
                        yield _sse({"type": "token", "content": exposed})
                elif event["event"] == "on_tool_start":
                    tool_calls += 1

            yield _sse({"type": "done", "tool_calls": tool_calls})

        except ValueError as exc:
            log.warning("chat error: %s", exc)
            yield _sse({"type": "error", "detail": str(exc)})
        except Exception as exc:
            log.exception("chat generation failed")
            yield _sse({"type": "error", "detail": str(exc)})
        finally:
            pii_masker.forget(message_key)

    return StreamingResponse(
        generate(message_key, body),
        media_type="text/event-stream",
    )
