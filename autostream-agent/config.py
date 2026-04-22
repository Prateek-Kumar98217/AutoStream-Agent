from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str
    db_dir: str
    vector_store_dir: str
    mock_backend: str

    @property
    def db_path(self) -> str:
        return os.path.join(self.db_dir, "mock_leads.db")

    @property
    def mock_backend_url(self) -> str:
        return os.path.join(self.mock_backend, "leads")

settings = AgentSettings()