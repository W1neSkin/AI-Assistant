import io
import pytest
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

# Import the documents router
from app.api.documents import router as docs_router
from app.api.documents import clear_documents  # Import the actual endpoint function
# We'll override the get_current_user dependency.
from app.auth.deps import get_current_user  
# Also override the ServiceContainer dependency.
from app.core.service_container import ServiceContainer

# --- Fake Dependencies for Testing ---

# Fake user to simulate authentication
class FakeUser:
    id = "test_user_id"

def fake_get_current_user():
    return FakeUser()

# Fake index service to simulate document operations
class FakeIndexService:
    def __init__(self):
        self.documents = {}

    async def index_document(self, content, filename, user_id):
        # Create a simple doc id
        doc_id = f"doc{len(self.documents) + 1}"
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

# Fake service container to wrap our FakeIndexService
class FakeServiceContainer:
    def __init__(self):
        self.index_service = FakeIndexService()

    @classmethod
    def get_instance(cls):
        # This method will be overridden to return our fake container.
        # (The override is done in the app fixture below.)
        pass

@pytest.fixture
def fake_container():
    return FakeServiceContainer()

# --- Pytest Fixtures to Build the Test App ---

@pytest.fixture
def app(fake_container):
    app = FastAPI()
    # Override the get_current_user dependency with our fake
    app.dependency_overrides[get_current_user] = fake_get_current_user
    # Override ServiceContainer.get_instance to use our fresh fake container
    app.dependency_overrides[ServiceContainer.get_instance] = lambda: fake_container
    # Create a new router with reordered routes to ensure /clear is matched before /{doc_id}
    new_router = APIRouter()
    new_router.add_api_route("/documents/clear", clear_documents, methods=["DELETE"])
    for route in docs_router.routes:
        if route.path != "/documents/clear":
            new_router.routes.append(route)
    app.include_router(new_router)
    yield app
    app.dependency_overrides = {}

@pytest.fixture
def client(app):
    return TestClient(app)

# --- Unit Tests for Documents Router ---

def test_upload_document_success(client, fake_container):
    # Clear any previous entries
    fake_container.index_service.documents.clear()
    file_content = b"Test file content"
    files = {"file": ("test.txt", file_content, "text/plain")}
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "id" in data
    # Verify that the document was added to the fake index service
    doc_id = data["id"]
    assert doc_id in fake_container.index_service.documents
    uploaded_doc = fake_container.index_service.documents[doc_id]
    assert uploaded_doc["filename"] == "test.txt"

def test_list_documents_empty(client, fake_container):
    fake_container.index_service.documents.clear()
    response = client.get("/documents/list")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_list_documents_with_document(client, fake_container):
    # Pre-populate with a document for the fake user
    fake_container.index_service.documents.clear()
    fake_container.index_service.documents["doc1"] = {
        "content": b"dummy",
        "filename": "dummy.txt",
        "user_id": "test_user_id",
        "active": True
    }
    response = client.get("/documents/list")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "doc1"
    assert data[0]["filename"] == "dummy.txt"

def test_delete_document_success(client, fake_container):
    fake_container.index_service.documents.clear()
    fake_container.index_service.documents["doc1"] = {
        "content": b"dummy",
        "filename": "dummy.txt",
        "user_id": "test_user_id",
        "active": True
    }
    response = client.delete("/documents/doc1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("status") == "success"
    # Verify that the document is removed
    assert "doc1" not in fake_container.index_service.documents

def test_clear_documents_success(client, fake_container):
    fake_container.index_service.documents.clear()
    # Add documents: two for test user and one for another user
    fake_container.index_service.documents["doc1"] = {
        "content": b"A",
        "filename": "a.txt",
        "user_id": "test_user_id",
        "active": True
    }
    fake_container.index_service.documents["doc2"] = {
        "content": b"B",
        "filename": "b.txt",
        "user_id": "test_user_id",
        "active": True
    }
    fake_container.index_service.documents["doc3"] = {
        "content": b"C",
        "filename": "c.txt",
        "user_id": "other_user",
        "active": True
    }
    response = client.delete("/documents/clear")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("status") == "success"
    # Only the document for the other user should remain
    assert "doc1" not in fake_container.index_service.documents
    assert "doc2" not in fake_container.index_service.documents
    assert "doc3" in fake_container.index_service.documents

def test_update_document_status_success(client, fake_container):
    fake_container.index_service.documents.clear()
    fake_container.index_service.documents["doc1"] = {
        "content": b"dummy",
        "filename": "dummy.txt",
        "user_id": "test_user_id",
        "active": True
    }
    payload = {"active": False}
    response = client.patch("/documents/doc1", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("status") == "success"
    # Verify the update of the document status
    assert fake_container.index_service.documents["doc1"]["active"] is False

def test_delete_document_not_found(client, fake_container):
    """Test deleting a non-existent document"""
    fake_container.index_service.documents.clear()
    response = client.delete("/documents/nonexistent")
    assert response.status_code == 500
    assert response.json()["detail"] == "Document not found" 