import pytest
from fastapi.testclient import TestClient
from typing import Generator
from app.main import app
from app.core.config import settings
from app.core.service_container import ServiceContainer

@pytest.fixture
def test_client() -> Generator:
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def test_container() -> ServiceContainer:
    container = ServiceContainer()
    # Initialize with test configurations
    await container.initialize_for_tests()
    return container 