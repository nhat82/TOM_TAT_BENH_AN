from langchain.agents.middleware.types import AgentState

class ChatbotAgentState(AgentState):
    patient_id: str
    query_count: int = 0