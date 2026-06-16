from pydantic_settings import BaseSettings
from pydantic import BaseModel, SecretStr

class ModelConfig(BaseModel): 
    model_name: str
    temperature: float = 0.0
    fallback_model_name: str | None = None
    
class Settings(BaseSettings): 
    db_url: SecretStr
    model_name: str 
    max_sql_row: int 
    max_output_string_length: int
    gemini_api_key = SecretStr
    
    summary_agent_model = ModelConfig(
        model_name="gemini-3.1-flash-lite"
    )
    chatbot_agent_model = ModelConfig(
        model_name="gemini-2.5-flash"
    )
    
    class Config: 
        env_file = ".env"
        env_file_encoding = "utf-8"
        
settings = Settings()