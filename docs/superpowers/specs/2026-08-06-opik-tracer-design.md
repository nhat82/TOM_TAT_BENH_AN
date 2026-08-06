# Opik tracer integration (replaces LangSmith)

## Context
Backend currently traces LangChain/LangGraph agent runs via LangSmith, wired purely
through env vars set in `app/core/config.py` (`LANGSMITH_*`). No explicit tracer
code exists elsewhere — LangChain auto-instruments when those env vars are present.

Team runs a self-hosted Opik instance (on cloud infra) with auth enabled
(API key + workspace required), so tracing must switch from env-var auto-instrument
to explicit Opik wiring: Opik's LangChain integration is callback-based, not
env-var-auto-instrumented like LangSmith.

## Design

### 1. Config (`app/core/config.py`)
Replace the four `langsmith_*` Settings fields with:

```python
opik_api_key: SecretStr = Field(env="OPIK_API_KEY")
opik_workspace: str = Field(env="OPIK_WORKSPACE")
opik_url_override: str = Field(env="OPIK_URL_OVERRIDE")
opik_project_name: str = Field(default="medical-app", env="OPIK_PROJECT_NAME")
```

Replace the trailing `os.environ["LANGSMITH_*"] = ...` block with the Opik
equivalents (`OPIK_API_KEY`, `OPIK_WORKSPACE`, `OPIK_URL_OVERRIDE`,
`OPIK_PROJECT_NAME`). The Opik SDK reads these directly from the environment —
no interactive `opik.configure()` call needed.

### 2. Tracer factory (`app/services/agent_package/tracing.py`, new file)
Two tracing layers, matching what LangSmith previously gave for free:

- **Callback tracer** — captures LangGraph internals (nodes/tool calls):

```python
from opik.integrations.langchain import OpikTracer

def get_opik_tracer(*, agent: str, thread_id: str, **metadata) -> OpikTracer:
    return OpikTracer(tags=[agent], metadata={"thread_id": thread_id, **metadata})
```

  A new tracer is created per request (no shared/module-level instance), same
  lifetime discipline as `audit_context`.

- **Function-level trace** — `@opik.track` decorates the router-level functions
  that actually invoke an agent, giving each request one top-level span:
  `generate_summary`, `refine_patient_summary` (`summary.py`), and the inner
  `generate()` closure in `chat()` (`chat.py`) — that closure is where the agent
  call happens in the streaming case, not `chat()` itself.

### 3. Router wiring (`chat.py`, `summary.py`)
Add the callback tracer to the LangGraph `config` dict passed to
`ainvoke`/`astream_events`:

```python
config = {
    "configurable": {"thread_id": pid},
    "callbacks": [get_opik_tracer(agent="summary-agent", thread_id=pid, patient_id=pid, endpoint="summary")],
}
```

Same pattern in `chat.py`'s `generate()`, and in `refine_patient_summary`
(thread_id `f"{pid}-refine"`, endpoint `"refine"`).

No masking-related changes needed: traces only see what already reaches the
model, which is already PII-masked via `masking_context`/`remask_text` before
this point — same property LangSmith traces had.

### 4. Dependencies & env template
- `requirements.txt`: remove `langsmith==0.10.10`, add `opik`.
- `.env.example`: remove the four `LANGSMITH_*` lines, add:
  ```
  OPIK_API_KEY=
  OPIK_WORKSPACE=
  OPIK_URL_OVERRIDE=
  OPIK_PROJECT_NAME=
  ```

## Out of scope
- No changes to masking, audit logging, or agent business logic.
- No dashboards/alerts setup in Opik itself — config only.
