
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import PIIMiddleware

from .tools import sql_tools
from .prompts import summary_system_prompt
from .schemas import SummaryAgentState
from .models import get_model


summary_agent = create_agent(
    model=get_model("local/qwen3:14b"),
    name="summary-agent",
    tools=sql_tools,
    system_prompt=summary_system_prompt,
    state_schema=SummaryAgentState,
    checkpointer=InMemorySaver(),
    middleware=[PIIMiddleware("url", strategy="redact", apply_to_input=True),]
)
