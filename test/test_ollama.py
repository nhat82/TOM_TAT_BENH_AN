from datetime import datetime

import requests
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware.types import AgentState

class TestAgentState(AgentState):
    pass

@tool
def get_weather(location: str) -> str:
    """Lấy thông tin thời tiết hiện tại theo tên địa điểm.

    Args:
        location: Tên thành phố, ví dụ 'Hanoi', 'Ho Chi Minh City'
    """
    try:
        geo_res = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1},
            timeout=5,
        ).json()

        if not geo_res.get("results"):
            return f"Không tìm thấy địa điểm '{location}'."

        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]
        
        weather_res = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
            timeout=5,
        ).json()

        current = weather_res.get("current_weather", {})
        temp = current.get("temperature")
        windspeed = current.get("windspeed")

        return f"Thời tiết tại {location}: {temp}°C, gió {windspeed} km/h."
    
    except Exception as e:
        return f"Lỗi khi lấy thời tiết: {e}"
    
@tool
def get_current_time() -> str:
    """Lấy ngày giờ hiện tại."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

model = ChatOllama(
    model="qwen3:14b", 
    base_url="...",
    temperature=1.0,
)

agent = create_agent(
    model=model,
    name="test_agent",
    tools=[get_weather, get_current_time],
    state_schema=TestAgentState,
    system_prompt="You are a helpful assistant.",
    checkpointer=InMemorySaver(),
)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "1"}}
    result = agent.invoke(
        {"messages": [("user", "Thời tiết ở Hà Nội hôm nay thế nào?")]},
        config=config,
    )
    print(result["messages"][-1].content)
