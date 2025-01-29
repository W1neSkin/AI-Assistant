import weaviate
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def create_vector_store():
    """Initialize Weaviate client and create schema"""
    try:
        logger.info(f"Connecting to Weaviate at: {settings.WEAVIATE_URL}")
        # For newer versions (v4+):
        client = weaviate.Client(url="http://weaviate:8080")
        
        # For older versions (v3.x):
        # client = weaviate.Client(
        #     "http://weaviate:8080"  # Positional argument without 'url' keyword
        # )
        
        # Define schema if not exists
        if not client.schema.contains("Documents"):
            class_obj = {
                "class": "Documents",
                "vectorizer": "none",  # Important for custom vectors
                "properties": [
                    {
                        "name": "text",
                        "dataType": ["text"],
                    },
                    {
                        "name": "filename",
                        "dataType": ["text"],
                    },
                    {
                        "name": "doc_id",
                        "dataType": ["text"],
                    },
                    {
                        "name": "chunk_id",
                        "dataType": ["int"],
                    },
                    {
                        "name": "active",
                        "dataType": ["boolean"],
                    }
                ],
                "vectorIndexConfig": {
                    "distance": "cosine",
                    "efConstruction": 128,
                    "maxConnections": 16,
                },
            }
            client.schema.create_class(class_obj)
        
        vector_store = WeaviateVectorStore(
            weaviate_client=client,
            index_name="Documents"
        )
        
        logger.info("Weaviate vector store initialized")
        return vector_store
        
    except Exception as e:
        logger.error(f"Error initializing Weaviate: {str(e)}")
        raise 