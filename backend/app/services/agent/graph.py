import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from typing import Annotated
from dotenv import load_dotenv

from app.services.agent.tools.query_tools import tools
from app.services.agent.prompts import SYSTEM_PROMPT

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

GEMINI_API_KEY=os.environ["GEMINI_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", api_key=GEMINI_API_KEY)

llm_with_tools = llm.bind_tools(tools)


def call_llm(state: AgentState):
    messages = state["messages"]
    if not any(isinstance(m, dict) and m.get("role") == "system" for m in messages):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"


workflow = StateGraph(AgentState)

workflow.add_node("agent", call_llm)
workflow.add_node("tools", ToolNode(tools))


workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

query = {"messages": [("user", "bàng quang, thận của BN0012 như thế nào trong lần chụp cắt lớp mới nhất?")]}

# Stream each node execution step-by-step
for chunk in app.stream(query, stream_mode="values"):
    last_msg = chunk["messages"][-1]
    
    # Beautifully display the thoughts vs actions vs observations
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        print(f"\n🤖 [AI Thought / Action]: {last_msg.tool_calls}")
    elif last_msg.type == "tool":
        print(f"\n🔌 [Database Observation]: {last_msg.content}")
    else:
        print(f"\n💬 [AI Response]: {last_msg.content}")