import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the auth router, dependency, models and security helpers
from app.api.auth import router as auth_router
from app.dependencies import get_db_service
from app.models.user import User
from app.utils.security import get_password_hash

# ---------------------------------------------------------------------------
# Fake database classes to override the DB dependency in tests
# ---------------------------------------------------------------------------
class FakeSession:
    def __init__(self, fake_db: dict):
        self.fake_db = fake_db

    async def scalar(self, query):
        """
        Since the auth endpoints always use a query like:
            select(User).where(User.username == some_value)
        we try to extract the username value from the first where clause.
        """
        username = None
        criteria = getattr(query, "_where_criteria", None)
        if criteria:
            clause = list(criteria)[0]
            try:
                # If clause.right is a bind parameter, use its .value
                username = clause.right.value
            except AttributeError:
                username = clause.right
        return self.fake_db.get(username)

    def add(self, user: User):
        self.fake_db[user.username] = user

    async def commit(self):
        # In our fake implementation, commit doesn't do anything.
        pass

class FakeSessionContext:
    """
    This class acts as an async context manager returning a FakeSession.
    """
    def __init__(self, fake_db: dict):
        self.fake_db = fake_db
        self.session = FakeSession(self.fake_db)

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        pass

class FakeDBService:
    def __init__(self, fake_db: dict):
        self.fake_db = fake_db

    def async_session(self):
        return FakeSessionContext(self.fake_db)

# ---------------------------------------------------------------------------
# Pytest fixtures to configure our FastAPI app and dependency override
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_db():
    # This will act as our in-memory "database" (a dict mapping usernames to User instances)
    return {}

@pytest.fixture
def app(fake_db):
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    # Override the get_db_service dependency so that the auth routes use our fake DB service.
    app.dependency_overrides[get_db_service] = lambda: FakeDBService(fake_db)
    yield app
    app.dependency_overrides.clear()

@pytest.fixture
def client(app):
    return TestClient(app)

# ---------------------------------------------------------------------------
# Tests for the auth routes
# ---------------------------------------------------------------------------
def test_login_success(client, fake_db):
    """
    Test for a successful login.
    Pre-populate the fake DB with a test user whose password is 'secret'.
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
    fake_db["testuser"] = test_user

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

def test_login_failure_wrong_password(client, fake_db):
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
    fake_db["testuser"] = test_user

    payload = {
        "username": "testuser",
        "password": "wrongpassword",
        "remember_me": False
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect username or password"

def test_register_success(client, fake_db):
    """
    Test successful registration of a new user.
    After registration, the fake DB should contain the new user.
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
    # Verify that the new user was added to the fake DB
    assert "newuser" in fake_db
    new_user = fake_db["newuser"]
    # Ensure that the password is hashed (i.e. not equal to the plain password)
    assert new_user.hashed_password != "password123"

def test_register_failure_existing_user(client, fake_db):
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
    fake_db["existinguser"] = existing_user

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

def test_register_failure_password_mismatch(client, fake_db):
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