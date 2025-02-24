import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the auth router, dependency, models and security helpers
from app.api.auth import router as auth_router
from app.dependencies import get_db_service
from app.models.user import User
from app.utils.security import get_password_hash
from tests.unit.api.common_fixtures import (
    MockDBService,
    mock_db
)


# Pytest fixtures to configure our FastAPI app and dependency override
@pytest.fixture
def app(mock_db):
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    # Override the get_db_service dependency so that the auth routes use our mock DB service.
    app.dependency_overrides[get_db_service] = lambda: MockDBService(mock_db)
    yield app
    app.dependency_overrides.clear()

@pytest.fixture
def client(app):
    return TestClient(app)


# Tests for the auth routes
def test_login_success(client, mock_db):
    """
    Test for a successful login.
    Pre-populate the mock DB with a test user whose password is 'secret'.
    """
    password = "secret"
    hashed = get_password_hash(password)
    test_user = User(
        username="testuser",
        hashed_password=hashed,
        use_cloud=True,
        enable_document_search=True,
        handle_urls=True,
        check_db=True
    )
    mock_db["testuser"] = test_user

    payload = {
        "username": "testuser",
        "password": "secret",
        "remember_me": False
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_failure_wrong_password(client, mock_db):
    """
    Test for a failed login due to incorrect password.
    """
    password = "secret"
    hashed = get_password_hash(password)
    test_user = User(
        username="testuser",
        hashed_password=hashed,
        use_cloud=True,
        enable_document_search=True,
        handle_urls=True,
        check_db=True
    )
    mock_db["testuser"] = test_user

    payload = {
        "username": "testuser",
        "password": "wrongpassword",
        "remember_me": False
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect username or password"

def test_register_success(client, mock_db):
    """
    Test successful registration of a new user.
    After registration, the mock DB should contain the new user.
    """
    payload = {
        "username": "newuser",
        "password": "password123",
        "confirm_password": "password123",
        "use_cloud": False,
        "enable_document_search": True,
        "handle_urls": False,
        "check_db": False
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["message"] == "User created successfully"
    # Verify that the new user was added to the mock DB
    assert "newuser" in mock_db
    new_user = mock_db["newuser"]
    # Ensure that the password is hashed (i.e. not equal to the plain password)
    assert new_user.hashed_password != "password123"

def test_register_failure_existing_user(client, mock_db):
    """
    Test registration failure when a user with the given username already exists.
    """
    password = "password123"
    hashed = get_password_hash(password)
    existing_user = User(
        username="existinguser",
        hashed_password=hashed,
        use_cloud=False,
        enable_document_search=True,
        handle_urls=False,
        check_db=False
    )
    mock_db["existinguser"] = existing_user

    payload = {
        "username": "existinguser",
        "password": "newpass",
        "confirm_password": "newpass",
        "use_cloud": False,
        "enable_document_search": True,
        "handle_urls": False,
        "check_db": False
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Username already registered"

def test_register_failure_password_mismatch(client, mock_db):
    """
    Test registration failure when the provided passwords do not match.
    """
    payload = {
        "username": "user1",
        "password": "pass1",
        "confirm_password": "pass2",
        "use_cloud": True,
        "enable_document_search": False,
        "handle_urls": True,
        "check_db": True
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Passwords do not match" 