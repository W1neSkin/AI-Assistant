import pytest
from app.utils.weaviate_client import create_vector_store
from app.services.index_service import LlamaIndexService
from llama_index.core.schema import TextNode
import uuid
import time
from typing import AsyncGenerator

@pytest.fixture(scope="module")
async def vector_store() -> AsyncGenerator:
    """Create a test vector store instance"""
    store = await create_vector_store()
    yield store
    # Cleanup after tests
    try:
        store.clear()
    except Exception:
        pass

@pytest.fixture(scope="module")
async def index_service(vector_store) -> AsyncGenerator:
    """Create index service with real vector store"""
    service = LlamaIndexService()
    service.vector_store = vector_store
    await service.initialize()
    yield service
    # Cleanup
    await service.clear_all_data()

@pytest.mark.asyncio
async def test_vector_store_basic_operations(vector_store):
    """Test basic vector store operations"""
    # Create test node
    node = TextNode(
        text="Test document content",
        metadata={
            "doc_id": str(uuid.uuid4()),
            "filename": "test.txt",
            "active": "true"
        }
    )
    
    # Test adding
    doc_ids = vector_store.add([node])
    assert len(doc_ids) == 1
    
    # Wait for indexing
    time.sleep(1)
    
    # Test querying
    results = vector_store.query(
        query_embedding=[0.1] * 384,  # Mock embedding vector
        similarity_top_k=1
    )
    assert len(results) == 1
    assert results[0].node.text == "Test document content"
    
    # Test deletion
    vector_store.delete(doc_ids[0])
    
    # Verify deletion
    results = vector_store.query(
        query_embedding=[0.1] * 384,
        similarity_top_k=1
    )
    assert len(results) == 0

@pytest.mark.asyncio
async def test_vector_store_batch_operations(vector_store):
    """Test batch operations"""
    # Create multiple test nodes
    nodes = [
        TextNode(
            text=f"Test document {i}",
            metadata={
                "doc_id": str(uuid.uuid4()),
                "filename": f"test{i}.txt",
                "active": "true"
            }
        )
        for i in range(5)
    ]
    
    # Test batch adding
    doc_ids = vector_store.add(nodes)
    assert len(doc_ids) == 5
    
    # Wait for indexing
    time.sleep(1)
    
    # Test batch querying
    results = vector_store.query(
        query_embedding=[0.1] * 384,
        similarity_top_k=5
    )
    assert len(results) == 5

@pytest.mark.asyncio
async def test_vector_store_metadata_filtering(vector_store):
    """Test metadata filtering in queries"""
    # Create nodes with different metadata
    nodes = [
        TextNode(
            text="Active document",
            metadata={
                "doc_id": str(uuid.uuid4()),
                "filename": "active.txt",
                "active": "true"
            }
        ),
        TextNode(
            text="Inactive document",
            metadata={
                "doc_id": str(uuid.uuid4()),
                "filename": "inactive.txt",
                "active": "false"
            }
        )
    ]
    
    vector_store.add(nodes)
    time.sleep(1)
    
    # Query with active filter
    results = vector_store.query(
        query_embedding=[0.1] * 384,
        filters={"active": "true"}
    )
    
    assert len(results) == 1
    assert results[0].node.metadata["active"] == "true"

@pytest.mark.asyncio
async def test_vector_store_similarity_search(index_service):
    """Test similarity search with real documents"""
    # Index test documents with varying content
    docs = [
        (b"Python is a programming language", "python.txt"),
        (b"Java is also a programming language", "java.txt"),
        (b"Dogs are pets", "dogs.txt")
    ]
    
    for content, filename in docs:
        await index_service.index_document(content, filename)
    
    time.sleep(1)  # Wait for indexing
    
    # Search for programming-related content
    results = await index_service.query("programming languages")
    
    # Verify semantic search works
    assert len(results) > 0
    programming_docs = [r for r in results if "programming" in r["text"].lower()]
    assert len(programming_docs) >= 2  # Should find both programming-related docs
    
    # Verify irrelevant content has lower score
    dog_docs = [r for r in results if "dogs" in r["text"].lower()]
    if dog_docs:
        assert dog_docs[-1]["similarity_score"] < programming_docs[0]["similarity_score"]

@pytest.mark.asyncio
async def test_vector_store_persistence(vector_store):
    """Test that data persists between connections"""
    # Add test data
    node = TextNode(
        text="Persistent test content",
        metadata={
            "doc_id": str(uuid.uuid4()),
            "filename": "persistent.txt",
            "active": "true"
        }
    )
    vector_store.add([node])
    time.sleep(1)
    
    # Create new connection
    new_store = await create_vector_store()
    
    # Verify data exists in new connection
    results = new_store.query(
        query_embedding=[0.1] * 384,
        similarity_top_k=1
    )
    assert len(results) == 1
    assert "Persistent test content" in results[0].node.text

@pytest.mark.asyncio
async def test_vector_store_error_handling(vector_store):
    """Test error handling in vector store operations"""
    # Test adding invalid node
    with pytest.raises(Exception):
        vector_store.add([None])
    
    # Test querying with invalid embedding
    with pytest.raises(Exception):
        vector_store.query(
            query_embedding=None,
            similarity_top_k=1
        )
    
    # Test deleting non-existent document
    try:
        vector_store.delete("non-existent-id")
    except Exception as e:
        assert "not found" in str(e).lower() 