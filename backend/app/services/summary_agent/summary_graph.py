import logging
import os

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# log = logging.getLogger(__name__)

from app.services.summary_agent.prompts import SYSTEM_PROMPT
from app.services.summary_agent.tools.query_tools import tools


def _extract_text(content) -> str:
    """Gemini can return content as a list of blocks instead of a plain string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return str(content)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=os.environ["GEMINI_API_KEY"],
    temperature=0,
)


async def run_summary(patient_id: str) -> str:
    """Queries the DB and fills in the summary template for the given patient."""
    system_content = (
        SYSTEM_PROMPT
        + f"\n\nThe current patient ID is: {patient_id}. Only query records for this patient."
    )
    # log.info("system_prompt (first 300 chars): %.300s", system_content)
    agent = create_agent(model=llm, tools=tools, system_prompt=system_content, debug=True)
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate the medical summary for patient {patient_id}.",
                }
            ]
        }
    )
    return _extract_text(result["messages"][-1].content)


async def run_refine(current_summary: str, instruction: str) -> str:
    """Refines an existing summary based on the user's instruction."""
    response = await llm.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "You are a medical assistant. Refine the given Vietnamese medical summary "
                    "according to the user's instruction. Keep the same template structure. "
                    "If data is not present, keep 'N/A'. Never add fabricated information."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Current summary:\n{current_summary}\n\n"
                    f"Instruction: {instruction}\n\n"
                    "Please provide the refined summary."
                ),
            },
        ]
    )
    return _extract_text(response.content)
