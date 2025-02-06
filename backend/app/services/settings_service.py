from typing import Optional
from app.models.settings import UserSettings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class SettingsService:
    def __init__(self, cache_service):
        self.cache_service = cache_service
        self.settings_key = "app:settings"

    async def get_settings(self) -> UserSettings:
        """Get settings from Redis or return defaults"""
        try:
            settings_json = await self.cache_service.get(self.settings_key)
            if settings_json:
                try:
                    return UserSettings.parse_raw(settings_json)
                except Exception as e:
                    logger.error(f"Error parsing settings JSON: {str(e)}")
                    return UserSettings()
            return UserSettings()  # Return defaults
        except Exception as e:
            logger.error(f"Error getting settings: {str(e)}")
            return UserSettings()  # Return defaults on error

    async def update_settings(self, settings: UserSettings) -> bool:
        """Save settings to Redis"""
        try:
            await self.cache_service.set(
                self.settings_key,
                settings.model_dump_json(),
                expire=None  # Don't expire
            )
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False 