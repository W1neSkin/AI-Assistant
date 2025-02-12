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
async def test_query_index(index_service):
    """Test querying the index"""
    # First index some test documents
    docs = [
        (b"First test document", "doc1.txt"),
        (b"Second test document", "doc2.txt"),
        (b"Third test document", "doc3.txt")
    ]
    
    for content, filename in docs:
        await index_service.index_document(content, filename)
    
    # Test querying
    results = await index_service.query("test document", max_results=2)
    assert len(results) == 2  # Should respect max_results
    assert all("filename" in r for r in results)
    assert all("text" in r for r in results)
    assert all("similarity_score" in r for r in results)

@pytest.mark.asyncio
async def test_get_documents(index_service):
    """Test retrieving document list"""
    # Index test documents
    docs = [
        (b"First document", "doc1.txt"),
        (b"Second document", "doc2.txt")
    ]
    
    for content, filename in docs:
        await index_service.index_document(content, filename)
    
    # Get document list
    documents = await index_service.get_documents()
    assert len(documents) == 2
    assert all("id" in doc for doc in documents)
    assert all("filename" in doc for doc in documents)
    assert all("active" in doc for doc in documents)

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
async def test_clear_all_data(index_service):
    """Test clearing all documents"""
    # Index some documents
    docs = [
        (b"First doc", "doc1.txt"),
        (b"Second doc", "doc2.txt")
    ]
    
    for content, filename in docs:
        await index_service.index_document(content, filename)
    
    # Clear all data
    await index_service.clear_all_data()
    
    # Verify all documents are removed
    documents = await index_service.get_documents()
    assert len(documents) == 0

@pytest.mark.asyncio
async def test_chunk_text():
    """Test text chunking functionality"""
    text = "This is a test. " * 100  # Create a long text
    chunks = LlamaIndexService.chunk_text(text)
    
    assert len(chunks) > 1  # Should create multiple chunks
    assert all(len(chunk) <= 512 for chunk in chunks)  # Default chunk size

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