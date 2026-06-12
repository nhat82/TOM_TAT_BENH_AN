import os
from typing import Annotated, Literal

from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from app.services.react_agent.prompts import SYSTEM_PROMPT
from app.services.react_agent.tools.query_tools import tools


class AgentState(BaseModel):
    messages: Annotated[list, add_messages]
    patient_id: str = ""


llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=os.environ["GEMINI_API_KEY"],
    temperature=0,
)


llm_with_tools = llm.bind_tools(tools)


def call_llm(state: AgentState):
    system_content = SYSTEM_PROMPT
    if state.patient_id:
        system_content += f"\n\nThe current patient ID is: {state.patient_id}. Only query records for this patient."
        system_content += f"The current date is {datetime.today().strftime("%Y-%m-%d")}"

    messages = state.messages
    if not any(isinstance(m, dict) and m.get("role") == "system" for m in messages):
        messages = [{"role": "system", "content": system_content}] + list(messages)

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    last_message = state.messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"


workflow = StateGraph(AgentState)
workflow.add_node("agent", call_llm)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

graph = workflow.compile(checkpointer=MemorySaver())