from elasticsearch import AsyncElasticsearch
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from app.core.config import settings
from app.utils.logger import setup_logger
import os

async def get_es_client():
    return AsyncElasticsearch(
        hosts=[f"http://{os.getenv('ES_HOST')}:{os.getenv('ES_PORT')}"],
        retry_on_timeout=True,
        request_timeout=30,
        max_retries=3
    )

async def create_vector_store():
    es_client = await get_es_client()
    
    # Create index if it doesn't exist
    index_name = "documents"
    exists = await es_client.indices.exists(index=index_name)
    if not exists:
        index_settings = {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "1s"
                }
            },
            "mappings": {
                "properties": {
                    "metadata": {
                        "properties": {
                            "filename": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword"
                                    }
                                }
                            },
                            "active": {"type": "boolean"},
                            "doc_id": {"type": "keyword"},
                            "created_at": {"type": "date"}
                        }
                    },
                    "text": {"type": "text"},
                    "vector": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
        await es_client.indices.create(index=index_name, body=index_settings)
    
    return ElasticsearchStore(
        es_client=es_client,
        index_name=index_name,
        embedding_dimension=384,
        distance_strategy="COSINE"
    ) 