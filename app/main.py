from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Path
from services.llama_service import LlamaIndexService
from utils.validators import FileValidator
from utils.logger import setup_logger
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import openai
from utils.cache import QueryCache
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Use the same logger setup as in llama_service
logger = setup_logger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'html', 'docx'}

class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(..., description="OpenAI API Key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI Model to use")
    ES_HOST: str = "elasticsearch"
    ES_PORT: int = 9200
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    CACHE_TTL: int = 3600  # 1 hour

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

try:
    settings = Settings()
    # Initialize OpenAI API key
    openai.api_key = settings.OPENAI_API_KEY
except Exception as e:
    logger.error(f"Failed to load settings: {str(e)}")
    logger.error("Make sure OPENAI_API_KEY is set in .env file")
    raise

# Initialize FastAPI app
app = FastAPI(title="Document Q&A Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
llama_service = LlamaIndexService()

class QueryRequest(BaseModel):
    question: str
    max_results: Optional[int] = Query(default=3, ge=1, le=10)

file_validator = FileValidator(ALLOWED_EXTENSIONS, settings.MAX_FILE_SIZE)

query_cache = QueryCache(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    ttl=settings.CACHE_TTL
)

class DocumentStatus(BaseModel):
    active: bool

class DocumentResponse(BaseModel):
    id: str
    filename: str
    active: bool

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        logger.info(f"Starting upload of file: {file.filename}")
        content = await file.read()
        
        logger.info("Validating file...")
        file_validator.validate_file(content, file.filename)
        
        logger.info("Indexing document...")
        await llama_service.index_document(content, file.filename)
        
        logger.info(f"Successfully processed file: {file.filename}")
        return JSONResponse(
            content={
                "status": "success",
                "message": "Document uploaded and indexed successfully",
                "filename": file.filename,
                "error": None
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )
    except HTTPException as he:
        logger.error(f"HTTP Exception during upload: {str(he)}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(he.detail),
                "filename": file.filename,
                "error": str(he.detail)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        logger.exception("Full traceback:")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "filename": file.filename,
                "error": str(e)
            }
        )

@app.post("/query")
async def query_document(query: QueryRequest):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Check cache first
        cached_response = await query_cache.get_cached_response(
            query.question,
            query.max_results
        )
        if cached_response:
            return cached_response
        
        # Call the async method
        response = await llama_service.query_index(
            query.question, 
            max_results=query.max_results
        )
        
        # Cache the response
        await query_cache.cache_response(
            query.question,
            query.max_results,
            response
        )
        
        return response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing query")

@app.get("/question/{query}")
async def get_answer(query: str):
    try:
        logger.info(f"Getting answer for query: {query}")
        
        # Log before getting context
        logger.info("Fetching context from LlamaIndexService...")
        context_response = await llama_service.query_index(query)
        logger.info(f"Received context response with {len(context_response['source_nodes'])} source nodes")
        
        # Log context text
        context_text = "\n".join([
            node["text"] for node in context_response["source_nodes"]
        ])
        logger.info(f"Combined context length: {len(context_text)} characters")
        
        # Log OpenAI request
        logger.info(f"Sending request to OpenAI with model: {settings.OPENAI_MODEL}")
        additional_info = "Please provide a detailed answer based on the context. Don't add any other information."
        prompt = f"Based on the following context, answer the question: {query}\n\nContext: {context_text}\n\n{additional_info}"
        
        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
            
            # Make the request
            openai_response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            logger.info("Received response from OpenAI")
            
            answer = openai_response.choices[0].message.content
            logger.info(f"Generated answer length: {len(answer)} characters")
            
            response_data = {
                "query": query,
                "answer": answer,
                "context": context_response
            }
            logger.info("Successfully prepared response")
            return response_data
            
        except Exception as openai_error:
            logger.error(f"OpenAI API error: {str(openai_error)}")
            logger.exception("OpenAI error details:")
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error: {str(openai_error)}"
            )
            
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        logger.exception("Full error traceback:")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )

@app.get("/health")
async def health_check():
    try:
        # Check if Elasticsearch is accessible
        await llama_service.vector_store.client.ping()
        return {"status": "healthy", "message": "Service is running"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        ) 

async def check_es_connection():
    try:
        # Make sure to await the ping operation
        await llama_service.vector_store.client.ping()
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        return False 

@app.delete("/clear-data")
async def clear_all_data():
    try:
        logger.info("Attempting to clear all data from Elasticsearch")
        # Delete all documents from the index
        await llama_service.clear_all_data()
        return {
            "status": "success",
            "message": "All data cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        logger.exception("Full error traceback:")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing data: {str(e)}"
        ) 

@app.get("/documents", response_model=List[DocumentResponse])
async def get_documents():
    try:
        logger.info("Fetching all documents")
        documents = await llama_service.get_documents()
        return documents
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        logger.exception("Full error traceback:")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching documents: {str(e)}"
        )

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    try:
        logger.info(f"Deleting document: {doc_id}")
        await llama_service.delete_document(doc_id)
        return {"status": "success", "message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        logger.exception("Full error traceback:")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

@app.patch("/documents/{doc_id}")
async def update_document_status(doc_id: str, status: DocumentStatus):
    try:
        logger.info(f"Updating document status: {doc_id} -> {status.active}")
        await llama_service.update_document_status(doc_id, status.active)
        return {"status": "success", "message": "Document status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating document status: {str(e)}")
        logger.exception("Full error traceback:")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating document status: {str(e)}"
        ) 

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 