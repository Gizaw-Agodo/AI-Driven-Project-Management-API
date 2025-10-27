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
        return f'postgresql+asyncpg://{self.POSTGRESS_USER}:{self.POSTGRESS_PASSWORD}@{self.POSTGRESS_HOST}:{self.POSTGRESS_PORT}/{self.POSTGRESS_DB}'
        
    model_config = SettingsConfigDict(env_file=".env", extra='allow')

settings = Settings()