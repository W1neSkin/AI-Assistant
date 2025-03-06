import pytest
from app.core.service_container import ServiceContainer

@pytest.mark.asyncio
async def test_service_container_initialization():
    """
    Test that the service container initializes correctly:
    1. Initialize the service container
    2. Verify all services are properly initialized
    3. Test basic functionality of each service
    """
    # 1. Initialize the service container
    container = await ServiceContainer.get_instance()
    
    # 2. Verify all services are properly initialized
    assert container.is_initialized() is True
    
    # Check that all required services are available
    assert container.llm_service is not None
    assert container.db_service is not None
    assert container.url_service is not None
    assert container.index_service is not None
    assert container.cache_service is not None
    assert container.qa_service is not None
    
    # 3. Test basic functionality of each service
    # Test DB service
    db_service = container.get_db_service()
    assert db_service is not None
    assert db_service.engine is not None
    assert db_service.async_session is not None
    
    # Test cache service
    assert container.cache_service._redis is not None
    
    # Test that the LLM service is initialized
    assert container.llm_service.current_provider is not None
    
    # Test that the index service is initialized
    assert container.index_service.vector_store is not None
    
    # Test that the QA service is initialized with all dependencies
    assert container.qa_service.llm_service is not None
    assert container.qa_service.index_service is not None
    assert container.qa_service.url_service is not None
    assert container.qa_service.cache_service is not None 