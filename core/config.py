# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# 1. Define the path to the project's root directory.
#    Path(__file__) is the path to this file (config.py).
#    .parent gives the directory it's in (core/).
#    .parent.parent gives the parent of that directory, which is our project root.
ROOT_DIR = Path(__file__).parent.parent

# 2. Define the full path to the .env file in the root.
ENV_FILE_PATH = ROOT_DIR / ".env"

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "API_KEY_NOT_FOUND"

    # 3. Explicitly tell pydantic-settings to load from that exact .env file path for local development.
    #    When deployed, it will automatically look for environment variables (secrets).
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, extra='ignore')

settings = Settings()