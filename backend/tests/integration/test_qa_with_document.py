import pytest
import os
from urllib.parse import quote
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_qa_with_document_context_integration(client, auth_headers, sample_text_file):
    """
    Test the QA functionality with document context:
    1. Upload a document with known content
    2. Ask a question related to the document content
    3. Verify the answer references information from the document
    """
    # 1. Upload a document with known content
    with open(sample_text_file, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("sample.txt", f, "text/plain")},
            headers=auth_headers
        )
    
    assert response.status_code == 200
    doc_data = response.json()
    doc_id = doc_data["id"]
    
    # Verify the document was uploaded
    response = client.get("/api/documents/list", headers=auth_headers)
    assert response.status_code == 200
    docs = response.json()
    assert any(doc["id"] == doc_id for doc in docs)
    
    # 2. Ask a question related to the document content
    question = "What is integration testing?"
    encoded_question = quote(question)
    
    response = client.get(
        f"/api/question/{encoded_question}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    answer_data = response.json()
    
    # 3. Verify the answer contains relevant information
    # The answer should mention integration testing since it's in our sample document
    assert "answer" in answer_data
    
    # The answer should contain information from the document
    # Note: This is a bit of a fuzzy test since the exact answer depends on the LLM
    # We're looking for keywords that should be in the response
    answer_lower = answer_data["answer"].lower()
    assert "integration" in answer_lower
    assert "test" in answer_lower
    
    # 4. Clean up - delete the document
    response = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 200 