from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

from app.services.agent_package.schemas.agent import ChatbotAgentState, _pin_first


def test_pin_first_keeps_existing_value():
    assert _pin_first("BA0001", "BA0002") == "BA0001"


def test_pin_first_accepts_first_value():
    assert _pin_first(None, "BA0001") == "BA0001"
    assert _pin_first("", "BA0001") == "BA0001"


def _noop_node(state: ChatbotAgentState) -> dict:
    return {}


def test_patient_id_pinned_across_turns_via_checkpointer():
    graph = (
        StateGraph(ChatbotAgentState)
        .add_node("noop", _noop_node)
        .set_entry_point("noop")
        .set_finish_point("noop")
        .compile(checkpointer=InMemorySaver())
    )
    config = {"configurable": {"thread_id": "thread-1"}}

    first = graph.invoke({"patient_id": "BA0001", "messages": []}, config=config)
    assert first["patient_id"] == "BA0001"

    second = graph.invoke({"patient_id": "BA9999", "messages": []}, config=config)
    assert second["patient_id"] == "BA0001"
