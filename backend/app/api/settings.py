from fastapi import APIRouter, HTTPException, Depends
from app.models.settings import UserSettings
from app.utils.logger import setup_logger
from app.core.service_container import ServiceContainer

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/settings")
async def get_settings(
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Get user settings"""
    try:
        if not services.is_initialized():
            logger.warning("Settings service not initialized")
            return UserSettings()

        settings = await services.settings_service.get_settings()
        return settings
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return UserSettings()  # Return defaults instead of error

@router.post("/settings")
async def update_settings(
    settings: UserSettings,
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Update user settings"""
    try:
        if not services.is_initialized():
            raise HTTPException(500, "Settings service not initialized")

        success = await services.settings_service.update_settings(settings)
        if not success:
            raise HTTPException(500, "Failed to save settings")
        
        # Update runtime services
        services.qa_service.handle_urls = settings.handle_urls
        services.qa_service.check_db_needs = settings.check_db
        
        return {"status": "success", "settings": settings.dict()}
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 