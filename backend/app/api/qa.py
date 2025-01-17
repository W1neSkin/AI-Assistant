from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from urllib.parse import unquote
import time
from app.services.index_service import LlamaIndexService
from app.utils.cache import QueryCache
from app.core.config import settings
from app.services.llm_factory import create_llm
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    max_results: Optional[int] = 3

class QueryResponse(BaseModel):
    answer: str
    context: Optional[Dict[str, Any]] = None

def is_russian(text: str) -> bool:
    """Check if text contains Russian characters."""
    try:
        # Handle URL-encoded text
        decoded_text = unquote(text)
        return any(ord(char) >= 1040 and ord(char) <= 1103 for char in decoded_text)
    except Exception:
        return False

def format_prompt(question: str, context: str) -> str:
    """Format prompt based on language."""
    if is_russian(question):
        return (
            "<s>[INST] Ты русскоязычный ассистент. "
            "Твоя задача - отвечать ТОЛЬКО на русском языке. "
            "Используй ТОЛЬКО информацию из предоставленного контекста. "
            "ВАЖНО: Отвечай ТОЛЬКО на русском языке, даже если контекст на английском. "
            "Если контекст на английском - переведи нужную информацию на русский. "
            "Если в контексте недостаточно информации, ответь: "
            "\"Извините, в предоставленном контексте недостаточно информации для ответа на этот вопрос.\"\n\n"
            f"Вопрос: {question}\n\n"
            f"Контекст: {context} [/INST]</s>"
        )
    else:
        return (
            "<s>[INST] You are a helpful assistant. "
            "Please provide a detailed answer based on the given context. "
            "Answer should be factual and based only on the provided context.\n\n"
            f"Question: {question}\n\n"
            f"Context: {context} [/INST]</s>"
        )

async def get_services():
    index_service = LlamaIndexService()
    await index_service.initialize()
    llm = await create_llm()
    query_cache = QueryCache(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        ttl=settings.CACHE_TTL
    )
    return index_service, llm, query_cache

@router.post("/query", response_model=QueryResponse)
async def query_document(
    query: QueryRequest,
    services: tuple = Depends(get_services)
):
    """Query documents with a question."""
    index_service, local_llm, query_cache = services
    
    try:
        # Check cache first
        cached_response = await query_cache.get(query.question)
        if cached_response:
            return QueryResponse(**cached_response)

        # Get relevant documents
        context = await index_service.query_index(
            query.question,
            max_results=query.max_results
        )
        
        # Format context text
        context_text = ' '.join([node['text'] for node in context['source_nodes']])
        
        # Format prompt based on language
        prompt = format_prompt(query.question, context_text)
        
        # Generate answer
        answer = await local_llm.generate_answer(prompt)
        
        response = QueryResponse(answer=answer, context=context)
        
        # Cache the response
        await query_cache.set(query.question, response.dict())
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/question/{query}")
async def get_answer(
    query: str,
    services: tuple = Depends(get_services)
):
    """Get an answer for a question."""
    index_service, local_llm, query_cache = services
    
    try:
        start_time = time.time()
        decoded_query = unquote(query)
        
        # Check cache first
        cached_response = await query_cache.get(decoded_query)
        if cached_response:
            return cached_response

        # Get relevant documents
        context = await index_service.query_index(decoded_query)
        
        # Format context text
        context_text = ' '.join([node['text'] for node in context['source_nodes']])
        
        # Format prompt based on language
        prompt = format_prompt(decoded_query, context_text)
        
        # Generate answer
        answer = await local_llm.generate_answer(prompt)
        
        response = {
            "answer": answer,
            "context": context,
            "time_taken": round(time.time() - start_time, 2)
        }
        
        # Cache the response
        await query_cache.set(decoded_query, response)
        
        return response
    except Exception as e:
        logger.error(f"Error processing query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 