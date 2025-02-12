import pytest
from fastapi.testclient import TestClient
from typing import Dict

@pytest.mark.asyncio
async def test_qa_endpoint_basic(initialized_app: TestClient, auth_headers: Dict):
    response = initialized_app.post(
        "/api/qa/answer",
        json={"query": "What is the test about?"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "context" in data

@pytest.mark.asyncio
async def test_qa_endpoint_with_document_context(initialized_app: TestClient, auth_headers: Dict):
    # First upload a test document
    with open("tests/test_files/test.pdf", "rb") as f:
        response = initialized_app.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers=auth_headers
        )
    assert response.status_code == 200
    
    # Now test QA with document context
    response = initialized_app.post(
        "/api/qa/answer",
        json={"query": "What does the document say?"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "source_nodes" in data["context"]

@pytest.mark.asyncio
async def test_qa_endpoint_with_url(initialized_app: TestClient, auth_headers: Dict):
    response = initialized_app.post(
        "/api/qa/answer",
        json={"query": "What's in http://test.com?"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data

@pytest.mark.asyncio
async def test_qa_endpoint_error_handling(initialized_app: TestClient, auth_headers: Dict):
    # Test empty query
    response = initialized_app.post(
        "/api/qa/answer",
        json={"query": ""},
        headers=auth_headers
    )
    assert response.status_code == 400
    
    # Test missing query
    response = initialized_app.post(
        "/api/qa/answer",
        json={},
        headers=auth_headers
    )
    assert response.status_code == 422 