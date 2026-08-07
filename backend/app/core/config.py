import os
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, SecretStr


class ModelConfig(BaseModel):
    model_name: str
    temperature: float = 0.0
    fallback_model_name: str | None = None

class Settings(BaseSettings):
    # directory
    base_dir: str = os.path.dirname(os.path.abspath(__file__))
    
    db_url: SecretStr = Field(alias="PG_URL")
    agent_db_url: SecretStr | None = Field(default=None, alias="AGENT_DB_URL")

    # Agent constraints
    max_sql_row: int = 1
    max_output_string_length: int = 999999999

    # Agent keys
    gemini_api_key: SecretStr = Field(env="GEMINI_API_KEY")
    openrouter_api_key: SecretStr = Field(env="OPENROUTER_API_KEY")

    chatbot_agent_model : ModelConfig = ModelConfig(model_name="gemini-3.1-flash-lite")
    summary_agent_model : ModelConfig = ModelConfig(model_name="gemini-3.1-flash-lite")

    opik_api_key: str | None = Field(default=None, env="OPIK_API_KEY")
    opik_workspace: str = Field(default="default", env="OPIK_WORKSPACE")
    opik_url_override: str = Field(env="OPIK_URL_OVERRIDE")
    opik_project_name: str = Field(default="medical-app", env="OPIK_PROJECT_NAME")

    # Cloud configuration
    cloud_url: str = Field(default="None", env="CLOUD_URL")
    
    # Other configuration
    @property
    def masked_fields(self) -> frozenset[str]:
        yaml_path = os.path.join(self.base_dir, "..", "..", "config", "backend.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            return frozenset(yaml.safe_load(f)["masked_fields"])

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True

settings = Settings()