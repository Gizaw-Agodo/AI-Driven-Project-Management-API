from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME : str = "ai-driven-project-management"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"


    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()