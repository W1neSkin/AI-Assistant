import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_document_upload(initialized_app: TestClient, auth_headers: Dict):
    with open("tests/test_files/test.pdf", "rb") as f:
        response = initialized_app.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "filename" in data

@pytest.mark.asyncio
async def test_document_list(initialized_app: TestClient, auth_headers: Dict):
    response = initialized_app.get(
        "/api/documents",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "filename" in data[0]
        assert "active" in data[0]

@pytest.mark.asyncio
async def test_document_delete(initialized_app: TestClient, auth_headers: Dict):
    # First upload a document
    with open("tests/test_files/test.pdf", "rb") as f:
        upload_response = initialized_app.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers=auth_headers
        )
    doc_id = upload_response.json()["id"]
    
    # Then delete it
    response = initialized_app.delete(
        f"/api/documents/{doc_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_document_status_update(initialized_app: TestClient, auth_headers: Dict):
    # First upload a document
    with open("tests/test_files/test.pdf", "rb") as f:
        upload_response = initialized_app.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers=auth_headers
        )
    doc_id = upload_response.json()["id"]
    
    # Update its status
    response = initialized_app.put(
        f"/api/documents/{doc_id}/status",
        json={"active": False},
        headers=auth_headers
    )
    
    assert response.status_code == 200 