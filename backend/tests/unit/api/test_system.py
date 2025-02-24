import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.system import router as system_router
from app.core.config import settings
from app.core.service_container import ServiceContainer
from tests.unit.api.common_fixtures import MockServiceContainer


# --- Pytest Fixtures for App and Client ---

@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(system_router)
    yield app

@pytest.fixture
def client(app):
    return TestClient(app)

# --- Tests for System Endpoints ---

def test_get_available_models(client):
    """
    Test that the GET /models endpoint returns the list of available models
    and the current provider as specified in the settings.
    """
    response = client.get("/models")
    assert response.status_code == 200, response.text
    data = response.json()
    # The models are defined by the ModelType enum: ["local", "cloud"]
    expected_models = ["local", "cloud"]
    assert data.get("models") == expected_models
    # The current provider returned should match the settings.
    assert data.get("current") == settings.LLM_PROVIDER

def test_switch_provider_success(monkeypatch, client):
    """
    Test switching the provider successfully.
    """
    mock_container = MockServiceContainer()
    
    async def mock_get_instance():
        return mock_container
    monkeypatch.setattr(ServiceContainer, "get_instance", mock_get_instance)
    
    payload = {"provider": "cloud"}
    response = client.post("/switch-provider", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    # Expect a success message with the same provider.
    assert data == {"status": "success", "provider": "cloud"}

def test_switch_provider_missing_provider(monkeypatch, client):
    """
    Test that missing the 'provider' in the payload leads to an error.
    Note: due to the try/except block in the endpoint, the missing provider
    is caught and re-raised as a 500 error.
    """
    mock_container = MockServiceContainer()
    
    async def mock_get_instance():
        return mock_container
    monkeypatch.setattr(ServiceContainer, "get_instance", mock_get_instance)
    
    payload = {}  # Missing the provider field
    response = client.post("/switch-provider", json=payload)
    # Expecting a 500 HTTP status code because the raised exception is caught.
    assert response.status_code == 500, response.text
    data = response.json()
    # Check that the error detail indicates the missing provider.
    assert "Missing provider" in data.get("detail", "")
