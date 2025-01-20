from fastapi import APIRouter, HTTPException
from backend.services.qa_service import QAService
from backend.models.chat_request import ChatRequest

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint"""
    try:
        response = await QAService.get_answer(
            query=request.message,
            model_type=request.model_type,
            enable_doc_search=request.enable_doc_search
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 