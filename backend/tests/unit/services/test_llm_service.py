import pytest
from unittest.mock import AsyncMock, patch
from app.services.llm_service import LLMService

# Test for initialize: Ensure that providers are created and initialized, and default provider is set.
@pytest.mark.asyncio
async def test_initialize():
    service = LLMService()
    fake_cloud = AsyncMock()
    fake_cloud.initialize.return_value = None
    fake_local = AsyncMock()
    fake_local.initialize.return_value = None

    with patch("app.services.llm_service.CloudLLM", return_value=fake_cloud), \
         patch("app.services.llm_service.LocalLLM", return_value=fake_local), \
         patch("app.services.llm_service.settings") as fake_settings:
        fake_settings.LLM_PROVIDER = "cloud"
        await service.initialize()
        # Verify that both providers are set.
        assert "cloud" in service.providers
        assert "local" in service.providers
        # Check that the default provider is set correctly.
        assert service.current_provider == "cloud"
        fake_cloud.initialize.assert_awaited_once()
        fake_local.initialize.assert_awaited_once()

# Test for close: Ensure that close() calls close on each provider.
@pytest.mark.asyncio
async def test_close():
    service = LLMService()
    fake_cloud = AsyncMock()
    fake_local = AsyncMock()
    fake_cloud.close.return_value = None
    fake_local.close.return_value = None
    service.providers = {"cloud": fake_cloud, "local": fake_local}
    await service.close()
    fake_cloud.close.assert_awaited()
    fake_local.close.assert_awaited()

# Test for change_provider: Success scenario.
@pytest.mark.asyncio
async def test_change_provider_success():
    service = LLMService()
    service.providers = {"cloud": AsyncMock(), "local": AsyncMock()}
    await service.change_provider("local")
    assert service.current_provider == "local"

# Test for change_provider: Invalid provider should raise ValueError.
@pytest.mark.asyncio
async def test_change_provider_invalid():
    service = LLMService()
    service.providers = {"cloud": AsyncMock(), "local": AsyncMock()}
    with pytest.raises(ValueError, match="Invalid provider"):
        await service.change_provider("invalid")

# Test for generate_answer: Success scenario, ensuring the current provider's generate_answer is called.
@pytest.mark.asyncio
async def test_generate_answer_success():
    service = LLMService()
    fake_provider = AsyncMock()
    fake_provider.generate_answer.return_value = "answer from provider"
    service.providers = {"cloud": fake_provider}
    service.current_provider = "cloud"
    result = await service.generate_answer("prompt text")
    fake_provider.generate_answer.assert_awaited_once_with("prompt text")
    assert result == "answer from provider"

# Test for generate_answer: No current provider should raise ValueError.
@pytest.mark.asyncio
async def test_generate_answer_no_provider():
    service = LLMService()
    service.providers = {"cloud": AsyncMock()}
    service.current_provider = None
    with pytest.raises(ValueError, match="No LLM provider selected"):
        await service.generate_answer("prompt text")

# Test for is_db_question: If the provider returns "true" in the response, then we expect a True result.
@pytest.mark.asyncio
async def test_is_db_question_true():
    service = LLMService()
    fake_provider = AsyncMock()
    fake_provider.generate_answer.return_value = "true"
    service.providers = {"cloud": fake_provider}
    service.current_provider = "cloud"
    with patch("app.services.llm_service.PromptGenerator.format_prompt_for_is_question", return_value="formatted prompt"):
        result = await service.is_db_question("Is it a DB question?")
        assert result is True

# Test for is_db_question: If the provider raises an exception, then is_db_question returns False.
@pytest.mark.asyncio
async def test_is_db_question_false_on_exception():
    service = LLMService()
    fake_provider = AsyncMock()
    fake_provider.generate_answer.side_effect = Exception("fail")
    service.providers = {"cloud": fake_provider}
    service.current_provider = "cloud"
    with patch("app.services.llm_service.PromptGenerator.format_prompt_for_is_question", return_value="formatted prompt"):
        result = await service.is_db_question("Is it a DB question?")
        assert result is False

# Test for get_provider: When current_provider is "cloud", should return providers["cloud"].
def test_get_provider_cloud():
    service = LLMService()
    fake_cloud = AsyncMock()
    service.providers = {"cloud": fake_cloud, "local": AsyncMock()}
    service.current_provider = "cloud"
    provider = service.get_provider()
    assert provider == fake_cloud

# Test for get_provider: For other provider values.
def test_get_provider_local():
    service = LLMService()
    fake_local = AsyncMock()
    service.providers = {"cloud": AsyncMock(), "local": fake_local}
    service.current_provider = "local"
    provider = service.get_provider()
    assert provider == fake_local

# Test for the current_provider property (getter & setter).
def test_current_provider_property():
    service = LLMService()
    service.current_provider = "cloud"
    assert service.current_provider == "cloud" 