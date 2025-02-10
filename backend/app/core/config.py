from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Set, Literal

class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = "local"
    OPENAI_API_KEY: str = Field("", description="OpenAI API Key")
    OPENAI_MODEL: str = Field("gpt-3.5-turbo", description="OpenAI Model to use")
    DEEPSEEK_API_KEY: str = Field("", description="DeepSeek API Key")
    DEEPSEEK_MODEL: str = Field("deepseek/deepseek-r1:free", description="DeepSeek Model to use")
    TEMPERATURE: float = Field(0.7, ge=0.0, le=1.0)
    MAX_TOKENS: int = 6144
    LLM_MODEL_PATH: str = Field(
        "/app/storage/models/llm/mistral.gguf",
        description="Path to local LLM model file"
    )
    LLM_MODEL_NAME: str = "deepseek-r1:7b"
    
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
    POSTGRES_USER: str = Field("dbuser", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field("dbpass", description="PostgreSQL password")
    POSTGRES_DB: str = Field("customerdb", description="PostgreSQL database name")
    POSTGRES_HOST: str = Field("postgres", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(5432, description="PostgreSQL port")

    # URL Settings
    URL_FETCH_TIMEOUT: int = Field(10, description="Timeout for URL fetching in seconds")
    MAX_URL_CONTENT_SIZE: int = Field(5 * 1024 * 1024, description="Max URL content size (5MB)")
    URL_CACHE_TTL: int = Field(3600, description="URL cache TTL in seconds")

    # Database settings
    DATABASE_URL: str = "postgresql://dbuser:dbpass@postgres:5432/customerdb"
    
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