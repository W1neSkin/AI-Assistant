import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import router and dependencies used in the settings endpoints
from app.api.settings import router as settings_router
from app.dependencies import get_db_service
from app.auth.deps import get_current_user
from tests.unit.api.common_fixtures import (
    FakeDBService,
    fake_db,
    fake_user
)

@pytest.fixture
def app(fake_db, fake_user):
    app = FastAPI()
    # Override get_current_user to always return our fake user
    app.dependency_overrides[get_current_user] = lambda: fake_user
    # Override get_db_service to use our FakeDBService with fake_db
    app.dependency_overrides[get_db_service] = lambda: FakeDBService(fake_db)
    # Include the settings router (no prefix so that endpoints remain /settings)
    app.include_router(settings_router)
    yield app
    app.dependency_overrides.clear()

@pytest.fixture
def client(app):
    return TestClient(app)

# --- Unit Tests for Settings Endpoints ---

def test_get_settings(client, fake_user):
    """
    Test retrieving settings. The returned JSON should match
    the properties of the fake user.
    """
    response = client.get("/settings")
    assert response.status_code == 200, response.text
    expected = {
        "use_cloud": fake_user.use_cloud,
        "enable_document_search": fake_user.enable_document_search,
        "handle_urls": fake_user.handle_urls,
        "check_db": fake_user.check_db,
    }
    assert response.json() == expected

def test_update_settings(client, fake_db, fake_user):
    """
    Test updating settings. The endpoint should update the fake user's settings,
    return the expected success message and update the fake DB.
    """
    # Prepare new settings values
    payload = {
        "use_cloud": False,
        "enable_document_search": True,
        "handle_urls": False,
        "check_db": True
    }
    response = client.post("/settings", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data.get("status") == "success"
    # The returned settings should mirror the payload
    assert data.get("settings") == payload

    # Verify that the fake DB was updated with the user's new settings
    assert fake_user.username in fake_db
    updated_user = fake_db[fake_user.username]
    assert updated_user.use_cloud == payload["use_cloud"]
    assert updated_user.enable_document_search == payload["enable_document_search"]
    assert updated_user.handle_urls == payload["handle_urls"]
    assert updated_user.check_db == payload["check_db"] 