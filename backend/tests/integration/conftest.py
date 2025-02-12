import pytest
from typing import Dict, Generator
from fastapi.testclient import TestClient
from app.main import app
from app.core.service_container import ServiceContainer
from app.core.jwt import create_access_token
from tests.mocks.service_mocks import MockUser

@pytest.fixture
def test_client() -> Generator:
    with TestClient(app) as client:
        yield client

@pytest.fixture
def auth_headers() -> Dict[str, str]:
    access_token = create_access_token({"sub": "testuser"})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
async def initialized_app(test_client):
    # Initialize services with test configuration
    container = ServiceContainer.get_instance()
    await container.initialize_for_tests()
    return test_client 