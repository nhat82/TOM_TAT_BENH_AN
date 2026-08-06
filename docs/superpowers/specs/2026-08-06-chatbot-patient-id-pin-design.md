# Pin patient_id in chat agent state

## Problem

`ChatbotAgentState.patient_id` (schemas/agent.py) has no LangGraph reducer, so
it uses the default overwrite behavior. Every `/api/chat` call re-sends
`patient_id` from the client and passes it into `input_state`. On each
invoke, LangGraph merges this into the checkpointed thread state and
overwrites the existing value — even mid-conversation, even if the new value
is wrong.

Combined with the LLM being able to pass its own `patient_id` into
`run_sql_query`'s `parameters` (fixed separately in sql_tools.py), this made
the agent vulnerable to jumping between patients within one conversation
thread. The state-level fix closes the gap at its source: once a thread has
a patient_id, no later call — buggy client, stale frontend state, retried
request — can change it.

## Design

Add a reducer to `patient_id` that keeps the first value set for a thread
and ignores all later writes:

```python
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
```

`SummaryAgentState` inherits the same pin — same class of bug applies there
(thread_id = patient_id, same InMemorySaver pattern in summary.py router).

No router or tool changes needed: routers already send `patient_id` on
every call, which is required for the first turn (fresh thread, no
checkpoint yet) and harmless — now inert — on later turns.

## Testing

Existing tests under `backend/tests/` don't cover agent state directly.
Add a unit test exercising `_pin_first` and one exercising
`ChatbotAgentState`'s merge behavior via a fake/real checkpointer round
trip (invoke twice with different `patient_id`, assert the second is
ignored).

## Out of scope

- Removing client-resent `chat_history` (separate, larger API-contract
  change; not requested here).
- Any change to `sql_tools.py` merge order (already fixed).
