import pytest


#Fake DB Service and Session for Testing
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
    
    async def commit(self):
        # No operation needed for fake commit
        pass

    async def refresh(self, user):
        # No operation needed for fake refresh
        pass

    def add(self, user):
        # Simply store the user in the fake DB (dict) keyed by username
        self.fake_db[user.username] = user

class FakeSessionContext:
    def __init__(self, fake_db: dict):
        self.fake_db = fake_db
        self.session = FakeSession(fake_db)

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        pass

class FakeDBService:
    def __init__(self, fake_db: dict):
        self.fake_db = fake_db

    def async_session(self):
        return FakeSessionContext(self.fake_db)

# Fake User for Testing Settings Endpoints
class FakeUser:
    def __init__(self):
        self.id = "test_user_id"
        self.username = "testuser"
        self.use_cloud = True
        self.enable_document_search = False
        self.handle_urls = True
        self.check_db = False

# Fake QA Service for a successful response
class FakeQAService:
    async def get_answer(self, query, user):
        return {"answer": f"Answer for '{query}'", "username": user.username}

# Fake QA Service that raises an error
class FakeQAServiceError:
    async def get_answer(self, query, user):
        raise Exception("Fake error")

# Fake index service to simulate document operations
class FakeIndexService:
    def __init__(self):
        self.documents = {}

    async def index_document(self, content, filename, user_id):
        # Create a simple doc id
        doc_id = f"doc{len(self.documents) + 1}"
        self.documents[doc_id] = {
            "content": content,
            "filename": filename,
            "user_id": user_id,
            "active": True
        }
        return doc_id

    async def get_user_documents(self, user_id):
        return [
            {"id": key, "filename": doc["filename"], "active": doc["active"]}
            for key, doc in self.documents.items() if doc["user_id"] == user_id
        ]

    async def delete_document(self, doc_id, user_id):
        if doc_id in self.documents and self.documents[doc_id]["user_id"] == user_id:
            del self.documents[doc_id]
        else:
            raise Exception("Document not found")

    async def clear_user_documents(self, user_id):
        self.documents = {
            k: v for k, v in self.documents.items() if v["user_id"] != user_id
        }

    async def update_document_status(self, doc_id, active):
        if doc_id in self.documents:
            self.documents[doc_id]["active"] = active
        else:
            raise Exception("Document not found")
        
# Fake LLM Service for Testing
class FakeLLMService:
    async def change_provider(self, provider: str):
        # For a successful case, simply store the provider
        self.provider = provider

# Fake container to mimic ServiceContainer
class FakeServiceContainer:
    def __init__(self, qa_service=None, llm_service=None, index_service=None):
        self.qa_service = qa_service if qa_service is not None else FakeQAService()
        self.llm_service = llm_service if llm_service is not None else FakeLLMService()
        self.index_service = index_service if index_service is not None else FakeIndexService()

    async def initialize(self):
        # Do nothing for initialization in tests
        pass

    @classmethod
    def get_instance(cls):
        # This method will be overridden to return our fake container.
        # (The override is done in the app fixture below.)
        pass


def fake_get_current_user():
    return FakeUser()

# --- Pytest Fixtures ---

@pytest.fixture
def fake_db():
    # Our in-memory "database"
    return {}

@pytest.fixture
def fake_user():
    # Return a single fake user instance
    return FakeUser()
