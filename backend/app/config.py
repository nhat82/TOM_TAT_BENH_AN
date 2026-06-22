import os
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, SecretStr

class ModelConfig(BaseModel): 
    model_name: str
    temperature: float = 0.0
    fallback_model_name: str | None = None
    
class Settings(BaseSettings):
    db_url: SecretStr = Field(alias="PG_URL")
    max_sql_row: int = 1
    max_output_string_length: int = 999999999
    gemini_api_key: SecretStr = Field(alias="GEMINI_API_KEY")
    langsmith_api_key: SecretStr = Field(alias="LANGSMITH_API_KEY")
    langsmith_tracing: SecretStr = Field(alias="LANGSMITH_TRACING")
    chatbot_agent_model : ModelConfig = ModelConfig(model_name="gemini-3.1-flash-lite")
    summary_agent_model : ModelConfig = ModelConfig(model_name="gemini-3.1-flash-lite")
    langsmith_project: str = Field(default="medical-app", alias="LANGSMITH_PROJECT")
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True
        
settings = Settings()

os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
os.environ["LANGSMITH_TRACING"] = settings.langsmith_tracing.get_secret_value()
os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint