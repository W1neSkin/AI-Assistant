from app.core.config import settings
from app.llm.local_llm import LocalLLM
from app.llm.cloud_llm import CloudLLM
from app.utils.logger import setup_logger
from fastapi import HTTPException


logger = setup_logger(__name__)

async def create_llm(model_type: str = None):
    """Create LLM instance based on configuration."""
    try:
        # Use provided model_type or fallback to settings
        model = model_type.lower() if model_type else settings.LLM_PROVIDER
        logger.info(f"Creating LLM with model type: {model}")
        
        if model == "cloud":
            if not settings.LLM_API_KEY:
                raise ValueError("LLM API key is not configured")
            return CloudLLM()
        return LocalLLM(model_name=settings.LLM_LOCAL_MODEL)
    except Exception as e:
        logger.error(f"Error creating LLM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize model: {str(e)}"
        ) 