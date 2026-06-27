from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "IntelliCircuit Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:aryaan@localhost:5432/intellicircuit",
        description="Async PostgreSQL connection string"
    )
    
    GEMINI_API_KEY: str = Field(..., description="API Key for Google GenAI Services")
    
    # Use the clean, standardized production strings for the new SDK
    PRIMARY_MODEL: str = Field(default="gemini-2.5-flash", description="Primary AI compiler engine")
    FALLBACK_MODEL: str = Field(default="gemini-1.5-flash", description="Secondary fallback engine")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()