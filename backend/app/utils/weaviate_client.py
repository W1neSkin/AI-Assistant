import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.config import VectorDistances
from app.core.config import settings
from app.utils.logger import setup_logger
from llama_index.vector_stores.weaviate import WeaviateVectorStore

logger = setup_logger(__name__)

async def create_vector_store():
    """Initialize Weaviate client and create schema"""
    try:
        logger.info(f"Connecting to Weaviate at: {settings.WEAVIATE_URL}")
        # For newer versions (v4+):
        client = weaviate.connect_to_local(
            host='weaviate',
            port=8080,
            grpc_port=50051,
        )
        
        # Create collection if not exists
        if not client.collections.exists("Documents"):
            client.collections.create(
                name="Documents",
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="filename", data_type=DataType.TEXT),
                    Property(name="doc_id", data_type=DataType.TEXT),
                    Property(name="chunk_id", data_type=DataType.INT),
                    Property(name="active", data_type=DataType.TEXT)
                ],
                vectorizer_config=Configure.Vectorizer.none(),  # We provide our own vectors
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                    ef_construction=128,
                    max_connections=64
                )
            )
            logger.info("Created Documents collection")
        else:
            logger.info("Documents collection already exists")
            
        # Create and return WeaviateVectorStore instance
        vector_store = WeaviateVectorStore(
            weaviate_client=client,
            index_name="Documents",
            text_key="text"
        )
        logger.info("Weaviate vector store initialized")
        return vector_store
        
    except Exception as e:
        logger.error(f"Error initializing Weaviate: {str(e)}")
        raise 