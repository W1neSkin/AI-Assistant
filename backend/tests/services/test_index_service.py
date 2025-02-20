import warnings

# Suppress Pydantic v2 deprecation warnings from llama-index
warnings.filterwarnings(
    "ignore",
    message="Support for class-based `config` is deprecated",
    category=DeprecationWarning
)

import pytest
from unittest.mock import Mock, patch
from app.services.index_service import LlamaIndexService
from llama_index.core.schema import TextNode
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

class MockEmbedding(BaseEmbedding):
    def _get_text_embedding(self, text: str) -> list:
        return [0.1, 0.2, 0.3]  # Dummy embedding

    def _get_query_embedding(self, query: str) -> list:
        return [0.1, 0.2, 0.3]  # Dummy embedding
        
    async def _aget_text_embedding(self, text: str) -> list:
        return [0.1, 0.2, 0.3]  # Dummy embedding

    async def _aget_query_embedding(self, query: str) -> list:
        return [0.1, 0.2, 0.3]  # Dummy embedding

@pytest.fixture
def mock_vector_store():
    mock = Mock()
    mock.query.return_value = Mock()
    return mock

@pytest.fixture
def mock_embed_model():
    return MockEmbedding()

async def create_index_service(mock_vector_store, mock_embed_model):
    with patch('app.services.index_service.create_embedding_model', return_value=mock_embed_model):
        with patch('app.services.index_service.create_vector_store', return_value=mock_vector_store):
            service = LlamaIndexService()
            await service.initialize()
            return service

@pytest.mark.asyncio
async def test_index_document(mock_vector_store, mock_embed_model):
    # Initialize service
    service = await create_index_service(mock_vector_store, mock_embed_model)
    
    # Test data
    content = b"test content"
    filename = "test.txt"
    user_id = "user123"
    
    # Mock vector store response for document check
    service.vector_store.query.return_value.nodes = []
    
    # Test indexing
    doc_id = await service.index_document(content, filename, user_id)
    
    assert doc_id is not None
    assert service.vector_store.add.called

@pytest.mark.asyncio
async def test_query(mock_vector_store, mock_embed_model):
    # Initialize service
    service = await create_index_service(mock_vector_store, mock_embed_model)
    
    # Test data
    question = "test question"
    user_id = "user123"
    
    # Mock response nodes
    mock_node = TextNode(
        text="test response",
        metadata={
            "doc_id": "123",
            "filename": "test.txt",
            "chunk_id": 0,
            "total_chunks": 1
        }
    )
    
    # Setup mock returns
    service.vector_store.query.return_value.nodes = [mock_node]
    service.vector_store.query.return_value.similarities = [0.8]
    
    # Test query
    results = await service.query(question, user_id)
    
    assert len(results) == 1
    assert results[0]["filename"] == "test.txt"
    assert results[0]["similarity_score"] == 0.8

@pytest.mark.asyncio
async def test_get_user_documents(mock_vector_store, mock_embed_model):
    # Initialize service
    service = await create_index_service(mock_vector_store, mock_embed_model)
    
    # Test data
    user_id = "user123"
    
    # Mock response node
    mock_node = TextNode(
        text="test content",
        metadata={
            "doc_id": "123",
            "filename": "test.txt",
            "file_size": 100,
            "active": "true"
        }
    )
    
    # Setup mock returns
    service.vector_store.query.return_value.nodes = [mock_node]
    
    # Test getting user documents
    docs = await service.get_user_documents(user_id)
    
    assert len(docs) == 1
    assert docs[0]["filename"] == "test.txt"
    assert docs[0]["size"] == 100
    assert docs[0]["active"] is True

@pytest.mark.asyncio
async def test_delete_document(mock_vector_store, mock_embed_model):
    # Initialize service
    service = await create_index_service(mock_vector_store, mock_embed_model)
    
    # Test data
    doc_id = "123"
    user_id = "user123"
    
    # Mock response node
    mock_node = TextNode(
        text="test content",
        metadata={
            "doc_id": "123",
            "filename": "test.txt",
            "users": [user_id],  # Only one user
            "active": "true"
        }
    )
    
    # Setup mock returns
    service.vector_store.query.return_value.nodes = [mock_node]
    
    # Test deleting document for user
    await service.delete_document(doc_id, user_id)
    
    # Since this was the last user, verify the document was deleted with correct filter
    service.vector_store.delete.assert_called_with(
        filter=MetadataFilters(filters=[
            ExactMatchFilter(key="doc_id", value=doc_id)
        ])
    )

@pytest.mark.asyncio
async def test_delete_document_with_remaining_users(mock_vector_store, mock_embed_model):
    # Initialize service
    service = await create_index_service(mock_vector_store, mock_embed_model)
    
    # Test data
    doc_id = "123"
    user_id = "user123"
    other_user = "other_user"
    
    # Mock response node with multiple users
    mock_node = TextNode(
        text="test content",
        metadata={
            "doc_id": "123",
            "filename": "test.txt",
            "users": [user_id, other_user],
            "active": "true"
        }
    )
    
    # Setup mock returns
    service.vector_store.query.return_value.nodes = [mock_node]
    
    # Test deleting document for one user
    await service.delete_document(doc_id, user_id)
    
    # Verify document was updated with remaining users
    service.vector_store.update.assert_called_with(
        filter=MetadataFilters(filters=[
            ExactMatchFilter(key="doc_id", value=doc_id)
        ]),
        update={
            "users": [other_user]
        }
    ) 