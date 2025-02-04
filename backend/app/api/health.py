from fastapi import APIRouter, Request
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    logger.debug(f"Health check from: {request.client.host}")
    logger.debug(f"Headers: {request.headers}")
    return {"status": "healthy"} 