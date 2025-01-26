from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents_router, qa_router, health_router
from app.core.config import settings
from app.services.index_service import LlamaIndexService
from app.llm.local_llm import LocalLLM

app = FastAPI(title="Document Q&A Bot")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize services
llama_service = LlamaIndexService()
local_llm = LocalLLM(model_path="/app/storage/models/llm/mistral.gguf")

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(documents_router, tags=["documents"])
app.include_router(qa_router, tags=["qa"]) 