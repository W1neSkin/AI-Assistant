from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

def add_cors_middleware(app):
    """Add CORS middleware to the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 