from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME : str = "ai-driven-project-management"
    DEBUG: bool = True

    #postgress config 
    POSTGRESS_USER:str = 'postgress'
    POSTGRESS_PASSWORD: str = 'postgress'
    POSTGRESS_HOST : str = 'localhost'
    POSTGRESS_PORT : str = '5432'
    POSTGRESS_DB : str =  "project_management"

    @property
    def DATABASE_URL(self):
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()