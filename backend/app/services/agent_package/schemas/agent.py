from langchain.agents.middleware.types import AgentState

class PatientAgentState(AgentState):
    patient_id: str