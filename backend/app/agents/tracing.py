"""Opik tracing for agent runs.

Two layers, mirroring what LangSmith's env-var auto-instrument gave for free:

  1. `get_opik_tracer` — a LangChain callback that captures LangGraph internals
     (nodes, tool calls). A new instance per request.
  2. `opik.track` — decorate the router-level function that actually invokes
     an agent, for one top-level span per request.

Traces only see what already reaches the model, which is PII-masked upstream
via `masking_context`/`remask_text` — no extra scrubbing needed here.
"""

from __future__ import annotations

from opik.integrations.langchain import OpikTracer

__all__ = ["get_opik_tracer"]


def get_opik_tracer(*, agent: str, thread_id: str, **metadata) -> OpikTracer:
    return OpikTracer(tags=[agent], metadata={"thread_id": thread_id, **metadata})
