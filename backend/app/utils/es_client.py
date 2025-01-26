from elasticsearch import AsyncElasticsearch
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from app.core.config import settings
from app.utils.logger import setup_logger
import os
import json

logger = setup_logger(__name__)

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
        logger.info("Creating new Elasticsearch index with vector mapping")
        index_settings = {
            "mappings": {
                "properties": {
                    "metadata": {
                        "properties": {
                            "filename": {"type": "keyword"},
                            "doc_id": {"type": "keyword"},
                            "active": {"type": "boolean"}
                        }
                    },
                    "text": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "_2gram": {
                                "type": "text",
                                "analyzer": "custom_2gram"
                            },
                            "_3gram": {
                                "type": "text",
                                "analyzer": "custom_3gram"
                            }
                        }
                    },
                    "vector": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "custom_2gram": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "shingle_2gram"]
                        },
                        "custom_3gram": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "shingle_3gram"]
                        }
                    },
                    "filter": {
                        "shingle_2gram": {
                            "type": "shingle",
                            "min_shingle_size": 2,
                            "max_shingle_size": 2
                        },
                        "shingle_3gram": {
                            "type": "shingle",
                            "min_shingle_size": 3,
                            "max_shingle_size": 3
                        }
                    }
                }
            }
        }
        await es_client.indices.create(index=index_name, body=index_settings)
        logger.info("Index created successfully")
    
    # Debug: Check existing documents
    response = await es_client.search(
        index=index_name,
        body={
            "query": {"match_all": {}},
            "size": 1
        }
    )
    logger.info(f"Total documents in index: {response['hits']['total']['value']}")
    
    return ElasticsearchStore(
        es_client=es_client,
        index_name=index_name,
        embedding_dimension=384,
        distance_strategy="COSINE"
    ) 