from app.core.service_container import ServiceContainer
from app.services.db_service import DatabaseService

async def get_db_service() -> DatabaseService:
    """
    Dependency to get the DatabaseService instance.
    This handles the asynchronous initialization of the ServiceContainer.
    """
    service_container = await ServiceContainer.get_instance()
    return service_container.get_db_service() 