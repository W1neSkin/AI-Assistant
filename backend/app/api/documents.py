from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from app.core.config import settings
from app.services.index_service import LlamaIndexService
from app.utils.validators import FileValidator
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from app.core.service_container import ServiceContainer
from app.utils.logger import setup_logger

router = APIRouter()
file_validator = FileValidator(settings.ALLOWED_EXTENSIONS, settings.MAX_FILE_SIZE)
logger = setup_logger(__name__)

class DocumentStatus(BaseModel):
    active: bool

class DocumentResponse(BaseModel):
    id: str
    filename: str
    active: bool
    class Config:
        from_attributes = True

async def get_index_service() -> LlamaIndexService:
    service = LlamaIndexService()
    await service.initialize()
    return service

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    index_service: LlamaIndexService = Depends(get_index_service)
):
    """Upload and index a document."""
    try:
        logger.debug(f"Received upload request for file: {file.filename}")
        # Validate file
        content = await file.read()
        file_validator.validate_file(content, file.filename)
        
        logger.debug("File validation passed, indexing document")
        # Index document
        await index_service.index_document(content, file.filename)
        
        logger.debug("Document indexed successfully")
        return JSONResponse(
            content={
                "status": "success",
                "message": f"File {file.filename} uploaded and indexed successfully",
                "filename": file.filename
            },
            status_code=200
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def get_documents(
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Get list of all documents"""
    try:
        if not services.is_initialized():
            raise HTTPException(500, "Services not initialized")
            
        documents = await services.index_service.get_documents()
        logger.info(f"Retrieved {len(documents)} documents")
        return [DocumentResponse(**doc) for doc in documents]
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Delete a specific document"""
    try:
        await services.index_service.delete_document(doc_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/clear")
async def clear_documents(
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Clear all documents"""
    try:
        await services.index_service.clear_all_data()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error clearing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/documents/{doc_id}")
async def update_document_status(
    doc_id: str,
    active: bool,
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Update document active status"""
    try:
        await services.index_service.update_document_status(doc_id, active)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error updating document status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 