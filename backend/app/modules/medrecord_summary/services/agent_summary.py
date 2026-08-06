
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import PIIMiddleware

from app.agents.tools import sql_tools
from app.agents.schemas import SummaryAgentState
from app.agents.models import get_model
from .prompts import system_prompt as summary_system_prompt


summary_agent = create_agent(
    model=get_model("local/qwen3:14b"),
    name="summary-agent",
    tools=sql_tools,
    system_prompt=summary_system_prompt,
    state_schema=SummaryAgentState,
    checkpointer=InMemorySaver(),
    middleware=[PIIMiddleware("url", strategy="redact", apply_to_input=True),]
)
