from typing import Any, AsyncIterator

import opik
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import PIIMiddleware

from app.agents.models import get_model
from app.agents.tracing import get_opik_tracer
from app.agents.tools import sql_tools
from app.agents.prompts import chatbot_system_prompt
from app.agents.schemas import ChatbotAgentState


chatbot_agent = create_agent(
    # model=get_model("local/qwen3:14b"),
    model=get_model("api/gemini-3.1-flash-lite"),
    name="chatbot-agent",
    tools=sql_tools,
    system_prompt=chatbot_system_prompt,
    state_schema=ChatbotAgentState,
    checkpointer=InMemorySaver(),
    middleware=[PIIMiddleware("url", strategy="redact", apply_to_input=True),]
)

@opik.track("chatbot-agent", tags=["chatbot-agent"])
async def chat_streaming(
    patient_id: str,
    query: str,
    message_key: str,
) -> AsyncIterator[dict[str, Any]]:
    """Runs the chatbot agent and yields raw astream_events events.

    Multi-turn memory comes from the LangGraph checkpointer (thread_id=patient_id),
    not client-supplied history — dropped for now. Does not unmask output —
    that stays the caller's job.
    """
    input_state = {
        "patient_id": patient_id,
        "message_key": message_key,
        "messages": [{"role": "user", "content": query}],
    }
    tracer = get_opik_tracer(agent="chatbot-agent", thread_id=patient_id, patient_id=patient_id, endpoint="chat")
    config = {
        "configurable": {"thread_id": patient_id},
        "callbacks": [tracer] if tracer else [],
    }

    async for event in chatbot_agent.astream_events(input_state, config=config, version="v2"):
        yield event