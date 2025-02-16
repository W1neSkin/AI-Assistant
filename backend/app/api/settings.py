from fastapi import APIRouter, HTTPException, Depends

from app.models.settings import UserSettings
from app.utils.logger import setup_logger
from app.auth.deps import get_current_user
from app.models.user import User
from app.services.db_service import DatabaseService
from app.core.service_container import ServiceContainer
from app.dependencies import get_db_service


logger = setup_logger(__name__)
router = APIRouter()

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_user)
):
    """Get user settings"""
    try:
        return UserSettings(
            use_cloud=current_user.use_cloud,
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
    db_service: DatabaseService = Depends(get_db_service)
):
    """Update user settings"""
    logger.info(f"Updating settings for user: {current_user.username}")
    logger.info(f"Settings: {settings}")
    try:
        current_user.use_cloud = settings.use_cloud
        current_user.enable_document_search = settings.enable_document_search
        current_user.handle_urls = settings.handle_urls
        current_user.check_db = settings.check_db
        
        async with db_service.async_session() as db:
            db.add(current_user)
            await db.commit()
            await db.refresh(current_user)
        return {"status": "success", "settings": settings.model_dump()}
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 