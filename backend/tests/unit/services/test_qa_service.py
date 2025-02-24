import pytest
from unittest.mock import AsyncMock, patch
from app.services.qa_service import QAService

# A simple dummy user class with required attributes.
class DummyUser:
    def __init__(self, use_cloud=True, handle_urls=True, check_db=True, enable_document_search=True, id=1):
        self.use_cloud = use_cloud
        self.handle_urls = handle_urls
        self.check_db = check_db
        self.enable_document_search = enable_document_search
        self.id = id

@pytest.fixture
def dummy_user():
    return DummyUser()

# Test that initialize properly sets dependencies.
def test_initialize_qa_service():
    qa = QAService()
    fake_llm = AsyncMock()
    fake_index = AsyncMock()
    fake_url = AsyncMock()
    fake_cache = AsyncMock()
    qa.initialize(fake_llm, fake_index, fake_url, fake_cache)
    assert qa.llm_service == fake_llm
    assert qa.index_service == fake_index
    assert qa.url_service == fake_url
    assert qa.cache_service == fake_cache

# Test that close resets dependencies to None.
@pytest.mark.asyncio
async def test_close_qa_service():
    qa = QAService()
    qa.llm_service = AsyncMock()
    qa.index_service = AsyncMock()
    qa.url_service = AsyncMock()
    qa.cache_service = AsyncMock()
    await qa.close()
    assert qa.llm_service is None
    assert qa.index_service is None
    assert qa.url_service is None
    assert qa.cache_service is None

# Test get_answer in the success scenario.
@pytest.mark.asyncio
async def test_get_answer_success(dummy_user):
    qa = QAService()
    # Set up fake dependencies.
    fake_llm = AsyncMock()
    fake_llm.current_provider = "cloud"
    # Simulate a successful answer from the provider.
    fake_llm.generate_answer.return_value = {"answer": "dummy answer"}
    fake_llm.is_db_question.return_value = False
    fake_llm.change_provider.return_value = None

    fake_index = AsyncMock()
    # Simulate document query returning sample doc data.
    fake_index.query.return_value = {"source_nodes": [{"filename": "doc1.txt", "text": "doc content"}]}

    fake_url = AsyncMock()
    fake_url.extract_urls.return_value = ["http://example.com"]
    fake_url.fetch_url_content.return_value = "URL content"

    # Patch internal methods to simplify the flow.
    qa._get_db_data = AsyncMock(return_value={"sql_query": "SELECT * FROM table", "results": "db results"})
    qa._get_document_data = AsyncMock(return_value={"source_nodes": [{"filename": "doc1.txt", "text": "doc content"}]})
    qa._build_context = AsyncMock(return_value="combined context")

    # Patch the prompt generator to return a dummy prompt.
    with patch("app.services.qa_service.PromptGenerator.format_prompt", return_value="dummy prompt"):
        qa.initialize(fake_llm, fake_index, fake_url, None)
        response = await qa.get_answer("What is the answer?", dummy_user)
        
        # Since dummy_user.use_cloud is True and current provider is already "cloud", no model switch occurs.
        fake_llm.change_provider.assert_not_awaited()
        fake_llm.generate_answer.assert_awaited_once_with("dummy prompt")
        
        # Check response structure.
        assert "answer" in response
        assert response["answer"] == "dummy answer"
        assert "context" in response
        assert "source_nodes" in response["context"]
        assert "time_taken" in response["context"]
        qa._build_context.assert_awaited_once()

# Test get_answer when an exception occurs (simulating a failure in generate_answer)
@pytest.mark.asyncio
async def test_get_answer_exception(dummy_user):
    qa = QAService()
    fake_llm = AsyncMock()
    fake_llm.current_provider = "cloud"
    # Force generate_answer to raise an exception.
    fake_llm.generate_answer.side_effect = Exception("LLM error")
    
    fake_index = AsyncMock()
    fake_url = AsyncMock()
    qa.initialize(fake_llm, fake_index, fake_url, None)
    
    response = await qa.get_answer("What is the answer?", dummy_user)
    # The error response should be structured appropriately.
    assert response["answer"].startswith("Error:")
    assert response["context"]["source_nodes"] == []
    assert response["context"]["time_taken"] == 0
