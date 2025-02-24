import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.url_service import URLService

@pytest.fixture
def url_service():
    # Instantiate URLService with a dummy cache_service (None for simplicity)
    service = URLService(cache_service=None)
    # Replace the URLHandler instance with a dummy object.
    # Use MagicMock for synchronous methods and AsyncMock for async methods.
    fake_handler = MagicMock()
    fake_handler.extract_urls = MagicMock()
    fake_handler.fetch_url_content = AsyncMock()
    service.url_handler = fake_handler
    return service

@pytest.mark.asyncio
async def test_extract_urls(url_service):
    # Arrange: set expected return value for extract_urls.
    expected_urls = ["http://example.com", "https://example.org"]
    url_service.url_handler.extract_urls.return_value = expected_urls

    # Act: call extract_urls.
    result = await url_service.extract_urls("Check out http://example.com and https://example.org")

    # Assert: result matches expected value.
    url_service.url_handler.extract_urls.assert_called_once_with("Check out http://example.com and https://example.org")
    assert result == expected_urls

@pytest.mark.asyncio
async def test_fetch_url_content_success(url_service):
    # Arrange: simulate successful fetch with (content, None)
    url_service.url_handler.fetch_url_content.return_value = ("Fetched content", None)

    # Act: call fetch_url_content.
    result = await url_service.fetch_url_content("http://example.com")

    # Assert: result should be the content.
    url_service.url_handler.fetch_url_content.assert_awaited_once_with("http://example.com")
    assert result == "Fetched content"

@pytest.mark.asyncio
async def test_fetch_url_content_error(url_service):
    # Arrange: simulate error scenario (content is None, error message provided)
    url_service.url_handler.fetch_url_content.return_value = (None, "Error: Unable to fetch URL")
    
    # Patch logger to capture the error log.
    with patch("app.services.url_service.logger") as fake_logger:
        # Act: call fetch_url_content.
        result = await url_service.fetch_url_content("http://example.com")
        
        # Assert: error logged and result is None.
        fake_logger.error.assert_called_with("Error: Unable to fetch URL")
        assert result is None 