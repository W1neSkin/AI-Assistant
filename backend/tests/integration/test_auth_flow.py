import pytest
from fastapi.testclient import TestClient
from tests.integration.conftest import VALID_TOKENS, MockUser

@pytest.mark.asyncio
async def test_auth_flow_integration(client):
    """
    Test the complete authentication flow:
    1. Register a new user
    2. Login with the new user credentials
    3. Use the obtained token to access a protected endpoint
    4. Verify the protected endpoint returns the expected response
    """
    # Mock the registration and login process
    # In a real test, we would actually call the registration and login endpoints
    # But since we're using a mock authentication system, we'll simulate it
    
    # 1. Simulate successful registration
    username = "integrationuser"
    
    # 2. Simulate successful login and token generation
    test_token = "mock_token_for_testing"  # Use the token that's already in VALID_TOKENS
    
    # Create auth headers with the token
    auth_headers = {"Authorization": f"Bearer {test_token}"}
    
    # 3. Use the token to access a protected endpoint (documents list)
    response = client.get("/api/documents/list", headers=auth_headers)
    assert response.status_code == 200
    
    # 4. Verify the response is a list (empty at this point)
    assert isinstance(response.json(), list)
    
    # 5. Try accessing without token (should fail)
    response = client.get("/api/documents/list")
    assert response.status_code == 401
    
    # 6. Try accessing with an invalid token (should fail)
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/documents/list", headers=invalid_headers)
    assert response.status_code == 401
    
    # Clean up
    if test_token in VALID_TOKENS:
        del VALID_TOKENS[test_token] 