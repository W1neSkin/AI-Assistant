from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.qa import router as qa_router

__all__ = ['health_router', 'documents_router', 'qa_router'] 