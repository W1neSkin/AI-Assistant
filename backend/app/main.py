from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from app.api import documents_router, health_router
from app.api.settings import router as settings_router
from app.api.qa import router as qa_router
from app.api.system import router as system_router
from app.api.auth import router as auth_router
from app.utils.logger import setup_logger
from app.core.service_container import ServiceContainer
from app.middleware.cors import add_cors_middleware


logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Initialize services
        try:
            await ServiceContainer.get_instance()
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            raise
        
        yield
    finally:
        ...

app = FastAPI(title="AI Assistant", lifespan=lifespan)

# Add CORS middleware
add_cors_middleware(app)

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

# Include routers
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(documents_router, prefix="/api", tags=["documents"])
app.include_router(qa_router, prefix="/api", tags=["qa"])
app.include_router(system_router, prefix="/api", tags=["system"])
app.include_router(settings_router, prefix="/api", tags=["settings"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 