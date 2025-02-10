from fastapi import APIRouter, HTTPException, Depends
from app.models.settings import UserSettings
from app.utils.logger import setup_logger
from app.core.service_container import ServiceContainer
from app.auth.deps import get_current_user
from app.models.user import User
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user settings"""
    try:
        return UserSettings(
            use_openai=current_user.use_openai,
            enable_document_search=current_user.enable_document_search,
            handle_urls=current_user.handle_urls,
            check_db=current_user.check_db
        )
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings")
async def update_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user settings"""
    try:
        current_user.use_openai = settings.use_openai
        current_user.enable_document_search = settings.enable_document_search
        current_user.handle_urls = settings.handle_urls
        current_user.check_db = settings.check_db
        
        await db.commit()
        return {"status": "success", "settings": settings.model_dump()}
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 