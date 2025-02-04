from fastapi import APIRouter, Body, Depends, HTTPException, Request
from enum import Enum
from app.core.config import settings
from app.core.service_container import ServiceContainer
from app.utils.logger import setup_logger

class ModelType(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"

logger = setup_logger(__name__)

router = APIRouter()

@router.get("/models")
async def get_available_models():
    """Get list of available model types."""
    try:
        response = {
            "models": [model.value for model in ModelType],
            "current": settings.LLM_PROVIDER
        }
        logger.debug(f"Sending response for /models: {response}")
        return response
    except Exception as e:
        logger.exception("Exception occurred while getting models.")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/switch-provider")
async def switch_provider(
    request: Request,
    payload: dict = Body(...),
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Switch LLM provider between local and OpenAI"""
    try:
        logger.debug(f"Received switch provider request: {payload}")
        logger.debug(f"Request headers: {request.headers}")
        provider = payload.get("provider")
        if not provider:
            raise HTTPException(400, "Missing provider in request body")
        
        if not services.llm_service:
            await services.initialize()
            
        success = await services.llm_service.switch_provider(provider.lower())
        logger.debug(f"Switch provider result: {success}")
        response = {"status": "success" if success else "failed", "provider": provider}
        logger.debug(f"Sending response: {response}")
        return response
    
    except Exception as e:
        logger.exception("Error switching provider")
        raise HTTPException(status_code=500, detail=str(e)) 