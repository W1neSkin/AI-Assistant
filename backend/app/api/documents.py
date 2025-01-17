from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from app.core.config import settings
from app.services.index_service import LlamaIndexService
from app.utils.validators import FileValidator
from pydantic import BaseModel
from fastapi.responses import JSONResponse

router = APIRouter()
file_validator = FileValidator(settings.ALLOWED_EXTENSIONS, settings.MAX_FILE_SIZE)

class DocumentStatus(BaseModel):
    active: bool

class DocumentResponse(BaseModel):
    id: str
    filename: str
    active: bool

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
        # Validate file
        content = await file.read()
        file_validator.validate_file(content, file.filename)
        
        # Index document
        await index_service.index_document(content, file.filename)
        
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

@router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(
    index_service: LlamaIndexService = Depends(get_index_service)
):
    """Get list of all documents."""
    try:
        documents = await index_service.get_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    index_service: LlamaIndexService = Depends(get_index_service)
):
    """Delete a document by ID."""
    try:
        await index_service.delete_document(doc_id)
        return {"status": "success", "message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/documents/{doc_id}")
async def update_document_status(
    doc_id: str,
    status: DocumentStatus,
    index_service: LlamaIndexService = Depends(get_index_service)
):
    """Update document active status."""
    try:
        await index_service.update_document_status(doc_id, status.active)
        return {
            "status": "success",
            "message": "Document status updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/all")
async def delete_all_documents(
    index_service: LlamaIndexService = Depends(get_index_service)
):
    """Delete all indexed documents."""
    try:
        await index_service.clear_all_data()
        return {
            "status": "success",
            "message": "All documents deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 