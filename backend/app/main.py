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

logger = setup_logger(__name__)

app = FastAPI(title="Document Q&A Bot")
service_container = ServiceContainer.get_instance()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
async def root():
    """Root endpoint to verify server is running."""
    return {"status": "running"}

# Initialize services
llama_service = LlamaIndexService()
local_llm = LocalLLM(base_url="http://ollama:11434")

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(documents_router, tags=["documents"])
app.include_router(qa_router, prefix="/api", tags=["qa"])
app.include_router(system_router, prefix="/api", tags=["system"])
app.include_router(settings_router, prefix="/api", tags=["settings"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await service_container.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 