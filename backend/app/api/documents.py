from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.core.config import settings
from app.utils.validators import FileValidator
from pydantic import BaseModel, ConfigDict
from app.core.service_container import ServiceContainer
from app.utils.logger import setup_logger
from app.auth.deps import get_current_user

router = APIRouter()
file_validator = FileValidator(settings.ALLOWED_EXTENSIONS, settings.MAX_FILE_SIZE)
logger = setup_logger(__name__)

class DocumentStatus(BaseModel):
    active: bool

class DocumentResponse(BaseModel):
    id: str
    filename: str
    active: bool

    model_config = ConfigDict(from_attributes=True)

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    current_user: str = Depends(get_current_user),
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Upload and index a document."""
    try:
        logger.debug(f"Received upload request for file: {file.filename}")
        # Validate file
        content = await file.read()
        file_validator.validate_file(content, file.filename)
        
        logger.debug("File validation passed, indexing document")
        # Index document
        doc_id = await services.index_service.index_document(
            content=content,
            filename=file.filename,
            user_id=str(current_user.id)
        )
        
        logger.debug("Document indexed successfully")
        return {"id": doc_id}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/list")
async def list_documents(
    current_user: str = Depends(get_current_user),
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Get list of all documents"""
    try:
        docs = await services.index_service.get_user_documents(str(current_user.id))
        logger.info(f"Retrieved {len(docs)} documents")
        return docs
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: str = Depends(get_current_user),
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Delete a specific document"""
    try:
        await services.index_service.delete_document(doc_id, str(current_user.id))
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/clear")
async def clear_documents(
    current_user: str = Depends(get_current_user),
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Clear all documents for current user"""
    try:
        await services.index_service.clear_user_documents(str(current_user.id))
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error clearing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/documents/{doc_id}")
async def update_document_status(
    doc_id: str,
    status: DocumentStatus,
    services: ServiceContainer = Depends(ServiceContainer.get_instance)
):
    """Update document active status"""
    logger.debug(f"Updating document status for {doc_id} to {status.active}")
    try:
        await services.index_service.update_document_status(doc_id, status.active)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error updating document status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 