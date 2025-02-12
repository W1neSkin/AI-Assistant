import pytest
from fastapi.testclient import TestClient
from typing import Dict

@pytest.mark.asyncio
async def test_switch_provider(initialized_app: TestClient, auth_headers: Dict):
    response = initialized_app.post(
        "/api/system/switch-provider",
        json={"provider": "cloud"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["provider"] == "cloud"

@pytest.mark.asyncio
async def test_get_models(initialized_app: TestClient, auth_headers: Dict):
    response = initialized_app.get(
        "/api/system/models",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 