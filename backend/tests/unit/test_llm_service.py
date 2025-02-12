import pytest
from app.services.llm_service import LLMService
from tests.mocks.llm_responses import MockCloudLLM, MockLocalLLM

@pytest.mark.asyncio
async def test_llm_service_initialization():
    service = LLMService()
    service.providers["cloud"] = MockCloudLLM()
    service.providers["local"] = MockLocalLLM()
    
    await service.initialize()
    assert service.initialized is True
    assert service.current_provider == "local"  # Default provider

@pytest.mark.asyncio
async def test_llm_provider_switching():
    service = LLMService()
    service.providers["cloud"] = MockCloudLLM()
    service.providers["local"] = MockLocalLLM()
    await service.initialize()
    
    # Test switching to cloud
    await service.change_provider("cloud")
    assert service.current_provider == "cloud"
    
    # Test switching to local
    await service.change_provider("local")
    assert service.current_provider == "local"

@pytest.mark.asyncio
async def test_generate_answer():
    service = LLMService()
    service.providers["local"] = MockLocalLLM()
    await service.initialize()
    
    response = await service.generate_answer("Test prompt")
    assert isinstance(response, str)
    assert len(response) > 0 