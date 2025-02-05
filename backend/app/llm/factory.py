from app.core.config import settings
from app.llm.local_llm import LocalLLM
from app.llm.openai_llm import OpenAILLM
from app.utils.logger import setup_logger
from fastapi import HTTPException


logger = setup_logger(__name__)

async def create_llm(model_type: str = None):
    """Create LLM instance based on configuration."""
    try:
        # Use provided model_type or fallback to settings
        model = model_type.lower() if model_type else settings.LLM_PROVIDER
        logger.info(f"Creating LLM with model type: {model}")
        
        if model == "openai":
            if not settings.DEEPSEEK_API_KEY:
                raise ValueError("Deepseek API key is not configured")
            return OpenAILLM()
        return LocalLLM(model_name=settings.LLM_MODEL_NAME)
    except Exception as e:
        logger.error(f"Error creating LLM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize model: {str(e)}"
        ) 