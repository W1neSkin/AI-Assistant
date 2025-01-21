import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Dict, Any
from urllib.parse import unquote
from app.core.config import settings
from app.utils.logger import setup_logger
from enum import Enum
from app.core.service_container import ServiceContainer

logger = setup_logger(__name__)


class ModelType(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"

router = APIRouter()

@router.get("/question/{query}")
async def get_answer(
    query: str,
    x_model_type: str = Header(None, alias="X-Model-Type"),
    x_enable_doc_search: str = Header("true", alias="X-Enable-Doc-Search")
):
    """Get answer for the question"""
    try:
        # 1. Get QA service from container
        container = ServiceContainer.get_instance()     
        if not container.qa_service:
            await container.initialize()
        qa_service = container.qa_service        
        
        # 2. Process query and settings
        decoded_query = unquote(unquote(query))
        include_docs = x_enable_doc_search.lower() == "true"
        
        # 3. Get answer from QA service
        response = await qa_service.get_answer(
            question=decoded_query,
            model_type=x_model_type,
            include_docs=include_docs
        )
        
        return response
    except Exception as e:
        logger.error(f"Error processing query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_available_models():
    """Get list of available model types."""
    return {
        "models": [model.value for model in ModelType],
        "current": settings.LLM_PROVIDER
    } 