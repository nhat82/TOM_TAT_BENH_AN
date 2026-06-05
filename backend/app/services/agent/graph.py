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
import requests
import base64

from app.services.agent.tools.query_tools import tools
from app.services.agent.prompts import SYSTEM_PROMPT
from app.services.agent.prompts import FORCE_SYNTHESIS

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    query_calls: set[str]

MAX_NUM_QUERY_CALLS = 5
GEMINI_API_KEY=os.environ["GEMINI_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", api_key=GEMINI_API_KEY)

llm_with_tools = llm.bind_tools(tools)

def call_llm(state: AgentState):
    messages = state["messages"]
    if not any(isinstance(m, dict) and m.get("role") == "system" for m in messages):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    response = llm_with_tools.invoke(messages)

    # Track SQL queries here so should_continue can read them from state
    query_calls = set(state.get("query_calls", set()))
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "execute_sql_query":
                query = tool_call["args"].get("query")
                if query:
                    query_calls.add(query)

    return {"messages": [response], "query_calls": query_calls}


def should_continue(state: AgentState) -> Literal["tools", "__end__", "force_synthesis"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        if (len(state.get("query_calls", set())) >= MAX_NUM_QUERY_CALLS):
            return "force_synthesis"
        for tool_call in last_message.tool_calls: 
            if tool_call["name"] == "execute_sql_query" and tool_call["args"].get("query") in state["query_calls"]:
                return "force_synthesis"
        return "tools"
    return "__end__"

def force_synthesis(state: AgentState):
    messages_with_synthesis_instructions = state["messages"] + [{"role": "system", "content": FORCE_SYNTHESIS}]
    response = llm.invoke(messages_with_synthesis_instructions)
    return {"messages": [response]}

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_llm)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("force_synthesis", force_synthesis)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "force_synthesis": "force_synthesis",
        END: END,
    }
)
workflow.add_edge("tools", "agent")
workflow.add_edge("force_synthesis", END)

app = workflow.compile()

def save_mermaid_to_png(mermaid_str, output_filename):
    ascii_msg = mermaid_str.encode('ascii')
    base64_bytes = base64.b64encode(ascii_msg)
    base64_string = base64_bytes.decode('ascii')

    url = f"https://mermaid.ink/img/{base64_string}"
    response = requests.get(url)

    if response.status_code == 200:
        with open(output_filename, "wb") as f:
            f.write(response.content)
        print(f"Success! Saved to {output_filename}")
    else:
        print(f"Failed to fetch image. Status: {response.status_code}")

agent_graph = app

if __name__ == "__main__":
    mermaid_text = agent_graph.get_graph().draw_mermaid()
    save_mermaid_to_png(mermaid_text, "agent_graph.png")
    # query = {"messages": [("user", "bàng quang, thận của BN0012 như thế nào trong lần chụp cắt lớp mới nhất?")]}

    # for chunk in app.stream(query, stream_mode="values"):
    #     last_msg = chunk["messages"][-1]

    #     if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
    #         print(f"\n🤖 [AI Thought / Action]: {last_msg.tool_calls}")
    #     elif last_msg.type == "tool":
    #         print(f"\n🔌 [Database Observation]: {last_msg.content}")
    #     else:
    #         print(f"\n💬 [AI Response]: {last_msg.content}")
