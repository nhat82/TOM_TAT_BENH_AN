from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from ..tools import sql_tools
from ..prompts import summary_system_prompt
from ..schemas import SummaryAgentState
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import PIIMiddleware


summary_agent = create_agent(
    model=ChatGoogleGenerativeAI(
        model=settings.chatbot_agent_model.model_name, 
        api_key=settings.gemini_api_key,
        temperature=settings.chatbot_agent_model.temperature,
        ),
    name="summary-agent",
    tools=sql_tools, 
    system_prompt=summary_system_prompt,
    state_schema=SummaryAgentState, 
    checkpointer=InMemorySaver(), 
    middleware=[
        PIIMiddleware("url", strategy="redact", apply_to_input=True),
    ]
)