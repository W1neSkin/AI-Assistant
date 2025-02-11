from fastapi import APIRouter, HTTPException, Depends
from urllib.parse import unquote
from app.utils.logger import setup_logger
from app.core.service_container import ServiceContainer
from app.models.user import User
from app.auth.deps import get_current_user

logger = setup_logger(__name__)

router = APIRouter()

@router.get("/question/{query}")
async def get_answer(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """Get answer for the question"""
    try:
        logger.debug(f"Received question request: {query}")
        
        # 1. Get QA service from container
        container = ServiceContainer.get_instance()     
        if not container.qa_service:
            await container.initialize()
        qa_service = container.qa_service        
        
        # 2. Process query and settings
        decoded_query = unquote(query)
        logger.info(f"Processing query: {decoded_query}")
        
        # 3. Pass the user to get_answer to use their settings
        response = await qa_service.get_answer(decoded_query, current_user)
        
        return response
    except Exception as e:
        logger.error(f"Error processing query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 