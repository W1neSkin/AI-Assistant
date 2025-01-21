import logging
from app.services.llm_service import LLMService
from app.services.db_service import DatabaseService
from app.services.url_service import URLService
from app.services.index_service import LlamaIndexService
from app.services.language_service import LanguageService
from app.services.cache_service import CacheService
from app.services.sql_generator import SQLGenerator
from app.services.qa_service import QAService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

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
        self.qa_service = None

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

            # Initialize cache first as it's needed by URL service
            self.cache_service = CacheService()
            
            # Initialize URL service with cache
            self.url_service = URLService(self.cache_service)

            self.index_service = LlamaIndexService()
            await self.index_service.initialize()
            
            self.lang_service = LanguageService()
            
            self.qa_service = QAService()
            self.qa_service.initialize(
                self.llm_service,
                self.index_service,
                self.url_service,
                self.cache_service,
                self.lang_service
            )

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