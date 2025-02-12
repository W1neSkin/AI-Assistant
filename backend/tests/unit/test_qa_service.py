import pytest
from app.services.qa_service import QAService
from tests.mocks.service_mocks import MockLLMService, MockIndexService

@pytest.fixture
async def qa_service():
    service = QAService()
    service.llm_service = MockLLMService()
    service.index_service = MockIndexService()
    await service.llm_service.initialize()
    await service.index_service.initialize()
    return service

@pytest.mark.asyncio
async def test_qa_basic_query(qa_service):
    """Test basic question answering"""
    response = await qa_service.get_answer("What is the test about?")
    
    assert response is not None
    assert "answer" in response
    assert "context" in response
    assert isinstance(response["context"]["time_taken"], float)

@pytest.mark.asyncio
async def test_qa_with_document_search(qa_service):
    """Test QA with document search"""
    response = await qa_service.get_answer(
        "What does the document say about testing?"
    )
    
    assert response is not None
    assert "source_nodes" in response["context"]
    assert len(response["context"]["source_nodes"]) > 0

@pytest.mark.asyncio
async def test_qa_with_url_handling(qa_service):
    """Test QA with URL handling"""
    mock_user = MockUser()
    mock_user.handle_urls = True
    
    response = await qa_service.get_answer(
        "What's in this http://test.com link?",
        mock_user
    )
    
    assert response is not None
    assert "answer" in response
    # URL content should be included in the response

@pytest.mark.asyncio
async def test_qa_provider_switching(qa_service):
    """Test switching between local and cloud providers"""
    mock_user = MockUser()
    
    # Test with local provider
    mock_user.use_cloud = False
    local_response = await qa_service.get_answer("Test question", mock_user)
    
    # Test with cloud provider
    mock_user.use_cloud = True
    cloud_response = await qa_service.get_answer("Test question", mock_user)
    
    assert local_response is not None
    assert cloud_response is not None

@pytest.mark.asyncio
async def test_qa_error_handling(qa_service):
    """Test error handling in QA service"""
    # Test with None query
    response = await qa_service.get_answer(None)
    assert "error" in response["answer"].lower()
    
    # Test with empty query
    response = await qa_service.get_answer("")
    assert "error" in response["answer"].lower()

@pytest.mark.asyncio
async def test_qa_context_building(qa_service):
    """Test context building from multiple sources"""
    mock_user = MockUser()
    mock_user.enable_document_search = True
    mock_user.handle_urls = True
    mock_user.check_db = True
    
    response = await qa_service.get_answer(
        "What does http://test.com say about the document?",
        mock_user
    )
    
    assert response is not None
    assert "context" in response
    assert "source_nodes" in response["context"]

@pytest.mark.asyncio
async def test_build_context_method(qa_service):
    """Test the _build_context method directly"""
    doc_data = {
        "source_nodes": [{
            "text": "Test document content",
            "filename": "test.pdf"
        }]
    }
    url_data = {
        "contents": ["Test URL content"]
    }
    db_data = {
        "results": "Test DB results"
    }
    
    context = await qa_service._build_context(doc_data, url_data, db_data)
    
    assert "Test document content" in context
    assert "Test URL content" in context
    assert "Test DB results" in context 