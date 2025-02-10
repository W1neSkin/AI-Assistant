from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents_router, health_router
from app.api.settings import router as settings_router
from app.core.config import settings
from app.services.index_service import LlamaIndexService
from app.llm.local_llm import LocalLLM
from app.api.qa import router as qa_router
from app.api.system import router as system_router
from app.utils.logger import setup_logger
from app.core.service_container import ServiceContainer
from app.api import documents
from contextlib import asynccontextmanager
from app.core.init_db import init_db
from app.db.base import get_db, create_tables
from app.api import auth

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database with admin user on startup
    try:
        await create_tables()  # Create tables before initializing DB
        async for db in get_db():
            await init_db(db)
            break  # We only need one session
        
        # Initialize other services
        try:
            await service_container.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            raise
        
        yield
    finally:
        if 'db' in locals():
            await db.close()

app = FastAPI(title="Document Q&A Bot", lifespan=lifespan)
service_container = ServiceContainer.get_instance()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
async def root():
    """Root endpoint to verify server is running."""
    return {"status": "running", "api_version": "1.2.0"}

# Initialize services
llama_service = LlamaIndexService()
local_llm = LocalLLM(base_url="http://ollama:11434")

# Include routers
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(documents_router, prefix="/api", tags=["documents"])
app.include_router(qa_router, prefix="/api", tags=["qa"])
app.include_router(system_router, prefix="/api", tags=["system"])
app.include_router(settings_router, prefix="/api", tags=["settings"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 