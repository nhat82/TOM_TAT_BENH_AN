from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from ..config import settings
from ..tools import sql_tools
from ..prompts import chatbot_system_prompt
from ..schemas import PatientAgentState

chatbot_agent = create_agent(
    model=ChatGoogleGenerativeAI(
        model=settings.chatbot_agent_model.model_name, 
        api_key=settings.gemini_api_key,
        temperature=settings.chatbot_agent_model.temperature,
        ),
    tools=sql_tools, 
    system_prompt=chatbot_system_prompt,
    state_schema=PatientAgentState
)

# print(chatbot_agent.invoke({
#     "patient_id": "BN0012",          
#     "messages": [("user", "bệnh nhân bị gì?")]
# }))