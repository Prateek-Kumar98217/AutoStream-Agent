"""
This modules acts as the central configuration management for the entire application.
It uses pydantic_settings to load the environment variables safely along with type checking.
"""


from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    GEMINI_API_KEY: str
    DB_DIR: str
    STORE_DIR: str
    BASE_BACKEND: str

    @property
    def db_path(self) -> str:
        return os.path.join(self.DB_DIR, "mock_leads.db")

    @property
    def mock_backend_url(self) -> str:
        return os.path.join(self.BASE_BACKEND, "leads")

# Singleton of the AgentSettings class, used as the single source of truth for configuration.
settings = AgentSettings()