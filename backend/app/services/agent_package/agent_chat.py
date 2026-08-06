
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import PIIMiddleware

from .tools import sql_tools
from .prompts import chatbot_system_prompt
from .schemas import ChatbotAgentState
from .models import get_model


chatbot_agent = create_agent(
    model=get_model("local/qwen3:14b"),
    # model=get_model("api/gemini-3.1-flash-lite"),
    name="chatbot-agent",
    tools=sql_tools,
    system_prompt=chatbot_system_prompt,
    state_schema=ChatbotAgentState,
    checkpointer=InMemorySaver(),
    middleware=[PIIMiddleware("url", strategy="redact", apply_to_input=True),]
)
