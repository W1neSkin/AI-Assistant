from app.core.config import settings
from app.services.local_llm import LocalLLM
from app.services.openai_llm import OpenAILLM
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def create_llm(model_type: str = None):
    """Create LLM instance based on configuration."""
    try:
        # Use provided model_type or fallback to settings
        model = model_type.lower() if model_type else settings.LLM_PROVIDER
        logger.info(f"Creating LLM with model type: {model}")
        
        if model == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is not configured")
            return OpenAILLM()
        return LocalLLM(model_path="/app/storage/models/llm/mistral.gguf")
    except Exception as e:
        logger.error(f"Error creating LLM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize model: {str(e)}"
        ) 