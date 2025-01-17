from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Set, Literal

class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: Literal["local", "openai"] = "local"
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

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings() 