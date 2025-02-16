from app.services.llm_service import LLMService
from app.services.db_service import DatabaseService
from app.services.url_service import URLService
from app.services.index_service import LlamaIndexService
from app.services.cache_service import CacheService
from app.services.qa_service import QAService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ServiceContainer:
    _instance = None
    
    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            cls._instance = ServiceContainer()
            await cls._instance.initialize()
        return cls._instance

    def __init__(self):
        self.llm_service = None
        self.db_service = None
        self.url_service = None
        self.index_service = None
        self.cache_service = None
        self.qa_service = None
        self._initialized = False

    async def initialize(self):
        """Initialize all services"""
        try:
            # Initialize cache first as it's needed by URL service and settings
            self.cache_service = CacheService()
            await self.cache_service.initialize()
                        
            # Initialize LLM service
            self.llm_service = LLMService()
            await self.llm_service.initialize()

            # Initialize DB service
            self.db_service = DatabaseService()
            await self.db_service.initialize()


            # Initialize URL service with cache
            self.url_service = URLService(self.cache_service)

            self.index_service = LlamaIndexService()
            await self.index_service.initialize()
                        
            self.qa_service = QAService()
            self.qa_service.initialize(
                self.llm_service,
                self.index_service,
                self.url_service,
                self.cache_service
            )

            logger.info("All services initialized successfully")
            self._initialized = True

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

    def is_initialized(self) -> bool:
        """Check if all services are initialized"""
        return self._initialized
    
    def get_db_service(self) -> DatabaseService:
        """Get the database service"""
        logger.info("Getting database service")
        if not self.db_service:
            raise RuntimeError("Database service not initialized")
        return self.db_service
