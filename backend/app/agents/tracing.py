import opik
from opik.integrations.langchain import OpikTracer

from app.core.config import settings

opik.configure(
    api_key=settings.opik_api_key,
    workspace="nh-t",
    project_name=settings.opik_project_name,
    url_override=settings.opik_url_override,
)

def get_opik_tracer(*, agent: str, thread_id: str, **metadata) -> OpikTracer | None:
    return OpikTracer(tags=[agent], metadata={"thread_id": thread_id, **metadata})