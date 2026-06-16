from langchain.agents.middleware.types import AgentState

class SummaryAgentState(AgentState):
    patient_id: str
    db_called: bool = False
    current_summary: str = ""
    refinement_count: int = 0
    