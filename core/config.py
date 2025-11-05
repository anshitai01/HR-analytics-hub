# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "API_KEY_NOT_FOUND"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()