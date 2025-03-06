import pytest
import asyncio
import os
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import hashlib
from unittest.mock import MagicMock, AsyncMock
from fastapi import Depends, HTTPException, status, Request
from contextlib import asynccontextmanager

from app.main import app
from app.db.base import Base
from app.dependencies import get_db_service
from app.models.user import User
from app.utils.security import get_password_hash
from app.core.service_container import ServiceContainer
from app.auth.deps import get_current_user

# Test database URL (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Mock user for testing
class MockUser:
    def __init__(self, id, username):
        self.id = id
        self.username = username
        # Add additional attributes that the QA service might need
        self.use_cloud = True
        self.enable_document_search = True
        self.handle_urls = True
        self.check_db = True

# Create a mock user that will be used throughout the tests
MOCK_USER = MockUser(id="test_user_id", username="testuser")
MOCK_TOKEN = "mock_token_for_testing"

# Dictionary to store valid tokens for testing
VALID_TOKENS = {
    MOCK_TOKEN: MOCK_USER
}

# Mock index service for testing
class MockIndexService:
    def __init__(self):
        self.documents = {}
        self.vector_store = MagicMock()
        self.index = MagicMock()
        self.embed_model = MagicMock()
        self.node_parser = MagicMock()

    async def initialize(self):
        # No initialization needed for mock
        pass

    async def index_document(self, content, filename, user_id):
        # Create a simple doc id
        unique_str = f"{filename}:{len(content)}"
        doc_id = hashlib.md5(unique_str.encode()).hexdigest()
        
        self.documents[doc_id] = {
            "content": content,
            "filename": filename,
            "user_id": user_id,
            "active": True
        }
        return doc_id

    async def get_user_documents(self, user_id):
        return [
            {"id": key, "filename": doc["filename"], "active": doc["active"]}
            for key, doc in self.documents.items() if doc["user_id"] == user_id
        ]

    async def delete_document(self, doc_id, user_id):
        if doc_id in self.documents and self.documents[doc_id]["user_id"] == user_id:
            del self.documents[doc_id]
        else:
            raise Exception("Document not found")

    async def clear_user_documents(self, user_id):
        self.documents = {
            k: v for k, v in self.documents.items() if v["user_id"] != user_id
        }

    async def update_document_status(self, doc_id, active):
        if doc_id in self.documents:
            self.documents[doc_id]["active"] = active
        else:
            raise Exception("Document not found")
            
    async def close(self):
        # No cleanup needed for mock
        pass

# Mock LLM service for testing
class MockLLMService:
    def __init__(self):
        self._current_provider = "mock_provider"
        self.providers = {
            "mock_provider": MagicMock(),
            "cloud": MagicMock(),
            "local": MagicMock()
        }
        self.initialized = True
        
    async def initialize(self):
        # No initialization needed for mock
        pass
        
    async def get_completion(self, prompt, **kwargs):
        return f"Mock completion for: {prompt}"
        
    async def generate_answer(self, prompt):
        return f"Mock answer for: {prompt}"
        
    @property
    def current_provider(self):
        return self._current_provider
        
    @current_provider.setter
    def current_provider(self, value):
        self._current_provider = value
        
    def get_provider(self):
        return self.providers[self._current_provider]
        
    async def close(self):
        # No cleanup needed for mock
        pass

# Mock cache service for testing
class MockCacheService:
    def __init__(self):
        self._redis = MagicMock()
        self.host = 'redis'
        self.port = 6379
        
    async def initialize(self):
        # No initialization needed for mock
        pass
        
    async def get(self, key):
        return None
        
    async def set(self, key, value, ttl=None):
        pass
        
    async def delete(self, key):
        return True
        
    async def clear(self):
        return True
        
    async def close(self):
        # No cleanup needed for mock
        pass

# Mock session for database operations
class MockSession:
    def __init__(self):
        self.committed = False
        self.refreshed = False
        self.added_objects = []
        
    async def commit(self):
        self.committed = True
        
    async def refresh(self, obj):
        self.refreshed = True
        
    def add(self, obj):
        self.added_objects.append(obj)

# Mock database service for testing
class MockDBService:
    def __init__(self):
        self.engine = MagicMock()
        self.async_session = self._async_session_factory
        self.session = MockSession()
        
    def _async_session_factory(self):
        @asynccontextmanager
        async def _async_session():
            yield self.session
        return _async_session()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_db(test_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

# Mock QA service for testing
class MockQAService:
    def __init__(self):
        self.llm_service = None
        self.index_service = None
        self.url_service = None
        self.cache_service = None
        
    def initialize(self, llm_service, index_service, url_service, cache_service):
        self.llm_service = llm_service
        self.index_service = index_service
        self.url_service = url_service
        self.cache_service = cache_service
        
    async def get_answer(self, query, user):
        # Return different answers based on whether document search is enabled
        if user.enable_document_search:
            return {
                "answer": f"Answer for '{query}' with document search enabled: Integration testing is a type of software testing where individual units or components are combined and tested as a group. It verifies that different parts of the system work together correctly. This information was found in your documents.",
                "sources": [{"text": "Integration tests verify that different components work together correctly.", "filename": "sample.txt"}]
            }
        else:
            return {
                "answer": f"Answer for '{query}' without document search: Integration testing is a type of software testing where individual units or components are combined and tested as a group.",
                "sources": []
            }

# This is a synchronous fixture that depends on async fixtures
@pytest.fixture
def client(event_loop, test_engine):
    """Create a test client for the FastAPI application."""
    # Create mock services
    mock_index_service = MockIndexService()
    mock_qa_service = MockQAService()
    mock_llm_service = MockLLMService()
    mock_cache_service = MockCacheService()
    mock_db_service = MockDBService()
    
    # Override dependencies
    async def override_get_db_service():
        return mock_db_service
    
    # Override the get_current_user dependency to check for valid tokens
    async def override_get_current_user(request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Extract token from header
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        
        # Check if token is valid
        if token not in VALID_TOKENS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return VALID_TOKENS[token]
    
    # Override the ServiceContainer.get_instance method
    original_get_instance = ServiceContainer.get_instance
    
    async def mock_get_instance():
        container = await original_get_instance()
        # Replace services with our mocks
        container.index_service = mock_index_service
        container.qa_service = mock_qa_service
        container.llm_service = mock_llm_service
        container.cache_service = mock_cache_service
        container.db_service = mock_db_service
        
        # Initialize the QA service with the necessary dependencies
        container.qa_service.initialize(
            container.llm_service,
            container.index_service,
            container.url_service,
            container.cache_service
        )
        return container
    
    # Apply the overrides
    app.dependency_overrides[get_db_service] = override_get_db_service
    app.dependency_overrides[get_current_user] = override_get_current_user
    ServiceContainer.get_instance = mock_get_instance
    
    # Create a test client
    with TestClient(app) as client:
        yield client
    
    # Clear dependency overrides
    app.dependency_overrides.clear()
    ServiceContainer.get_instance = original_get_instance

@pytest.fixture
async def test_user(test_db):
    """Create a test user."""
    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        use_cloud=True,
        enable_document_search=True,
        handle_urls=True,
        check_db=True
    )
    
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    yield user
    
    # Clean up
    await test_db.delete(user)
    await test_db.commit()

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for the test user."""
    # Return a mock token that's in our VALID_TOKENS dictionary
    return {"Authorization": f"Bearer {MOCK_TOKEN}"}

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    # Create test_data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

@pytest.fixture
def sample_text_file(test_data_dir):
    """Create a sample text file for testing document upload."""
    file_path = os.path.join(test_data_dir, "sample.txt")
    
    # Create a sample text file with some content
    with open(file_path, "w") as f:
        f.write("This is a sample document for testing.\n")
        f.write("It contains information about integration testing.\n")
        f.write("Integration tests verify that different components work together correctly.\n")
    
    return file_path 