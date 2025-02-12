import pytest
from app.services.index_service import LlamaIndexService
from tests.mocks.vector_store_mocks import MockVectorStore
from llama_index.core.schema import TextNode
import uuid

@pytest.fixture
async def index_service():
    service = LlamaIndexService()
    service.vector_store = MockVectorStore()
    await service.initialize()
    return service

@pytest.mark.asyncio
async def test_index_document(index_service):
    """Test document indexing"""
    content = b"This is a test document content"
    filename = "test.txt"
    
    await index_service.index_document(content, filename)
    
    # Query to verify document was indexed
    results = await index_service.query("test document")
    assert len(results) > 0
    assert results[0]["text"] == "This is a test document content"
    assert results[0]["filename"] == filename

@pytest.mark.asyncio
async def test_delete_document(index_service):
    """Test document deletion"""
    # First index a document
    content = b"Document to delete"
    filename = "delete_me.txt"
    await index_service.index_document(content, filename)
    
    # Get documents to find its ID
    documents = await index_service.get_documents()
    doc_id = documents[0]["id"]
    
    # Delete the document
    await index_service.delete_document(doc_id)
    
    # Verify deletion
    updated_documents = await index_service.get_documents()
    assert len(updated_documents) == 0

@pytest.mark.asyncio
async def test_update_document_status(index_service):
    """Test updating document active status"""
    # Index a document
    content = b"Test document"
    filename = "status_test.txt"
    await index_service.index_document(content, filename)
    
    # Get document ID
    documents = await index_service.get_documents()
    doc_id = documents[0]["id"]
    
    # Update status to inactive
    await index_service.update_document_status(doc_id, False)
    
    # Query should not return results for inactive documents
    results = await index_service.query("test document")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_error_handling(index_service):
    """Test error handling in index operations"""
    # Test with invalid content
    with pytest.raises(Exception):
        await index_service.index_document(None, "test.txt")
    
    # Test with invalid document ID
    with pytest.raises(Exception):
        await index_service.delete_document("non-existent-id")

@pytest.mark.asyncio
async def test_hybrid_search(index_service):
    """Test hybrid search functionality"""
    # Index test documents
    docs = [
        (b"Python programming guide", "python.txt"),
        (b"Java programming tutorial", "java.txt"),
        (b"Python vs Java comparison", "comparison.txt")
    ]
    
    for content, filename in docs:
        await index_service.index_document(content, filename)
    
    # Test hybrid search
    results = await index_service.query(
        "python programming",
        hybrid=True
    )
    
    assert len(results) > 0
    # Python-related documents should have higher scores
    assert any("python" in r["text"].lower() for r in results) 

@pytest.mark.asyncio
async def test_metadata_filtering(index_service):
    """Test querying with metadata filters"""
    # Create documents with different metadata
    doc1 = TextNode(
        text="Test document 1",
        metadata={
            "doc_id": str(uuid.uuid4()),
            "filename": "test1.txt",
            "active": "true",
            "category": "test"
        }
    )
    doc2 = TextNode(
        text="Test document 2",
        metadata={
            "doc_id": str(uuid.uuid4()),
            "filename": "test2.txt",
            "active": "false",
            "category": "test"
        }
    )
    
    # Add documents to vector store
    index_service.vector_store.add([doc1, doc2])
    
    # Query with active filter
    results = await index_service.query("test document")
    assert len(results) == 1  # Should only return active document
    assert results[0]["filename"] == "test1.txt" 