from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Set, Literal

class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = "local"
    OPENAI_API_KEY: str = Field("", description="OpenAI API Key")
    OPENAI_MODEL: str = Field("gpt-3.5-turbo", description="OpenAI Model to use")
    TEMPERATURE: float = Field(0.7, ge=0.0, le=1.0)
    MAX_TOKENS: int = 512
    
    # Vector Store Settings
    ES_HOST: str = "elasticsearch"
    ES_PORT: int = 9200
    
    # File Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {'txt', 'pdf', 'html', 'docx'}
    
    # Cache Settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    CACHE_TTL: int = 3600  # 1 hour

    # URL Settings
    URL_FETCH_TIMEOUT: int = Field(10, description="Timeout for URL fetching in seconds")
    MAX_URL_CONTENT_SIZE: int = Field(5 * 1024 * 1024, description="Max URL content size (5MB)")
    URL_CACHE_TTL: int = Field(3600, description="URL cache TTL in seconds")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings() 