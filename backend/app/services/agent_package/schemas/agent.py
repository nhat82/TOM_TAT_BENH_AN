from langchain.agents.middleware.types import AgentState

class PatientAgentState(AgentState):
    patient_id: str    
class ChatbotAgentState(PatientAgentState):
    pass
class SummaryAgentState(PatientAgentState):
    db_called: bool = False
    current_summary: str = ""
    refinement_count: int = 0
    