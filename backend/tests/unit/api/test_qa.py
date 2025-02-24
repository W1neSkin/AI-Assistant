import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.qa import router as qa_router
from app.auth.deps import get_current_user
from app.core.service_container import ServiceContainer
from tests.unit.api.common_fixtures import (
    MockQAService,
    MockQAServiceError,
    MockServiceContainer,
    mock_get_current_user
)


# Pytest fixture for a container with a working QA service
@pytest.fixture
def mock_container_success():
    return MockServiceContainer(qa_service=MockQAService())

# Pytest fixture for a container with a failing QA service
@pytest.fixture
def mock_container_error():
    return MockServiceContainer(qa_service=MockQAServiceError())

# --- Set up the test application with dependency overrides ---

@pytest.fixture
def app():
    app = FastAPI()
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.include_router(qa_router, prefix="/qa")
    yield app
    app.dependency_overrides.clear()

@pytest.fixture
def client(app):
    return TestClient(app)

# --- Unit Tests for QA endpoint ---

def test_get_answer_success(monkeypatch, client, mock_container_success):
    # Override the ServiceContainer.get_instance to return our mock container with a working QA service.
    async def mock_get_instance():
        return mock_container_success
    monkeypatch.setattr(ServiceContainer, "get_instance", mock_get_instance)

    # URL-encoded query: "hello world" becomes "hello%20world"
    response = client.get("/qa/question/hello%20world")
    assert response.status_code == 200, response.text
    expected = {"answer": "Answer for 'hello world'", "username": "testuser"}
    assert response.json() == expected

def test_get_answer_failure(monkeypatch, client, mock_container_error):
    # Override ServiceContainer.get_instance to simulate an error scenario.
    async def mock_get_instance():
        return mock_container_error
    monkeypatch.setattr(ServiceContainer, "get_instance", mock_get_instance)

    response = client.get("/qa/question/somequery")
    # Since the QA service is designed to raise an error, we expect a 500 status code.
    assert response.status_code == 500, response.text
    data = response.json()
    # The error detail should contain the mock error message.
    assert "Mock error" in data["detail"] 