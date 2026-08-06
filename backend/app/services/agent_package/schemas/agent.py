from typing import Annotated

from langchain.agents.middleware.types import AgentState


def _pin_first(existing: str | None, new: str) -> str:
    """Once set for this thread, patient_id can't be changed by a later call."""
    return existing or new


class PatientAgentState(AgentState):
    patient_id: Annotated[str, _pin_first]

class ChatbotAgentState(PatientAgentState):
    pass
class SummaryAgentState(PatientAgentState):
    db_called: bool = False
    current_summary: str = ""
    refinement_count: int = 0
