import pytest
import os
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_document_lifecycle_integration(client, auth_headers, sample_text_file):
    """
    Test the complete document lifecycle:
    1. Upload a document
    2. List documents and verify the uploaded document is present
    3. Update document status
    4. Verify the document status was updated
    5. Delete the document
    6. Verify the document is no longer in the list
    """
    # 1. Upload a document
    with open(sample_text_file, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("sample.txt", f, "text/plain")},
            headers=auth_headers
        )
    
    # Print the response content to see the error details
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    
    assert response.status_code == 200
    doc_data = response.json()
    assert "id" in doc_data
    doc_id = doc_data["id"]
    
    # 2. List documents and verify the uploaded document is present
    response = client.get("/api/documents/list", headers=auth_headers)
    assert response.status_code == 200
    docs = response.json()
    
    assert len(docs) > 0
    assert any(doc["id"] == doc_id for doc in docs)
    
    # Get the document from the list
    doc = next((doc for doc in docs if doc["id"] == doc_id), None)
    assert doc is not None
    assert doc["filename"] == "sample.txt"
    assert doc["active"] is True  # Default should be active
    
    # 3. Update document status to inactive
    response = client.patch(
        f"/api/documents/{doc_id}",
        json={"active": False},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 4. Verify the document status was updated
    response = client.get("/api/documents/list", headers=auth_headers)
    assert response.status_code == 200
    docs = response.json()
    
    doc = next((doc for doc in docs if doc["id"] == doc_id), None)
    assert doc is not None
    assert doc["active"] is False
    
    # 5. Delete the document
    response = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # 6. Verify the document is no longer in the list
    response = client.get("/api/documents/list", headers=auth_headers)
    assert response.status_code == 200
    docs = response.json()
    
    assert not any(doc["id"] == doc_id for doc in docs) 