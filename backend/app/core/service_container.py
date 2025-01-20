import logging
from typing import Optional
from app.services.llm_service import LLMService
from app.services.db_service import DatabaseService
from app.services.url_service import URLService
from app.services.index_service import LlamaIndexService
from app.services.language_service import LanguageService
from app.services.cache_service import CacheService
from app.services.sql_generator import SQLGenerator

logger = logging.getLogger(__name__)

class ServiceContainer:
    _instance = None
    
    def __init__(self):
        self.llm_service = None
        self.db_service = None
        self.url_service = None
        self.index_service = None
        self.lang_service = None
        self.cache_service = None
        self.sql_generator = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = ServiceContainer()
        return cls._instance

    async def initialize(self):
        """Initialize all services"""
        try:
            # Initialize services in order
            self.llm_service = LLMService()
            await self.llm_service.initialize()

            self.db_service = DatabaseService()
            await self.db_service.initialize()

            # Initialize SQLGenerator after DB service
            self.sql_generator = SQLGenerator(
                schema=await self.db_service.get_schema(),
                llm_service=self.llm_service
            )
            await self.sql_generator.initialize()

            # Other services...
            self.url_service = URLService()
            self.index_service = LlamaIndexService()
            self.lang_service = LanguageService()
            self.cache_service = CacheService()

            await self.index_service.initialize()
            logger.info("All services initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            raise

    async def cleanup(self):
        """Cleanup services on shutdown"""
        try:
            logger.info("Cleaning up services...")
            await self.cache_service.close()
            await self.db_service.close()
            await self.index_service.close()
            logger.info("Services cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up services: {str(e)}") 