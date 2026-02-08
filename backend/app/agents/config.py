import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ERP Intelligence"
    API_V1_STR: str = "/api/v1"
    
    # Gemini / Google GenAI
    GEMINI_API_KEY: str
    MODEL_NAME: str = "gemini-1.5-flash"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../.env"), 
        env_ignore_empty=True,
        extra="ignore"
    )

settings = Settings()
