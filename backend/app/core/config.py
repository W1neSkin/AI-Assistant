from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Set
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Assistant API"
    
    # LLM Settings
    LLM_PROVIDER: str = "local"
    LLM_API_KEY: str = Field("", description="LLM API Key")
    LLM_MODEL: str = Field("google/gemini-2.0-flash-001", description="LLM Model to use")
    TEMPERATURE: float = Field(0.7, ge=0.0, le=1.0)
    MAX_TOKENS: int = 6144
    LLM_LOCAL_MODEL: str = Field("deepseek-r1:7b", description="Local LLM model name")
    
    # Search Settings
    DEFAULT_INCLUDE_DOCS: bool = Field(True, description="Include document search by default")
    
    # Vector Store Settings
    WEAVIATE_URL: str = "http://weaviate:8080"
    
    # File Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {'txt', 'pdf', 'html', 'docx'}
    
    # Cache Settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    CACHE_TTL: int = 3600  # 1 hour

    # Database Settings
    POSTGRES_USER: str = Field("", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field("", description="PostgreSQL password")
    POSTGRES_DB: str = Field("", description="PostgreSQL database name")
    POSTGRES_HOST: str = Field("postgres", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(5432, description="PostgreSQL port")
    DATABASE_URL: str = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB')}"

    # URL Settings
    URL_FETCH_TIMEOUT: int = Field(10, description="Timeout for URL fetching in seconds")
    MAX_URL_CONTENT_SIZE: int = Field(5 * 1024 * 1024, description="Max URL content size (5MB)")
    URL_CACHE_TTL: int = Field(3600, description="URL cache TTL in seconds")

    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    # JWT settings
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production!
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

class DebugSettings(BaseSettings):
    PROFILE_QUERIES: bool = Field(False, description="Profile database queries")
    LOG_LEVEL: str = Field("DEBUG", description="Logging level in debug mode")
    RELOAD_DELAY: float = Field(0.5, description="Delay for hot reload")

settings = Settings() 