from functools import lru_cache

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

load_dotenv()
from app.core.config import settings

_MODEL_NAMES = ["api/gemini-3.1-flash-lite", "local/qwen3:14b"]
_MODEL_API_URLS = {
    "api/gemini-3.1-flash-lite": "google/gemini-3.1-flash-lite",
}
_MODEL_CACHE = {}

@lru_cache(maxsize=None)
def get_model(model_name: str):
    if model_name not in _MODEL_NAMES:
        raise ValueError(f"Unsupported model name: {model_name}")
    
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]
    
    provider, model = model_name.split("/", 1)
    if provider == "api":
        model = ChatOpenAI(
            model=_MODEL_API_URLS.get(model_name, model_name),
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    
    else:
        model = ChatOllama(
            model=model,
            base_url=settings.cloud_url,
            temperature=settings.chatbot_agent_model.temperature,
        )
    
    _MODEL_CACHE[model_name] = model
    return model
        