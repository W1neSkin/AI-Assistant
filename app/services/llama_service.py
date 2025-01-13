from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    Settings,
    StorageContext
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from utils.es_client import create_vector_store
from utils.logger import setup_logger
from typing import Dict, Any, List
import tempfile
import os
from datetime import datetime

logger = setup_logger(__name__)

class LlamaIndexService:
    def __init__(self):
        self.vector_store = None
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-MiniLM-L3-v2"
        )
        Settings.embed_model = self.embed_model

    async def initialize(self):
        if self.vector_store is None:
            self.vector_store = await create_vector_store()

    async def index_document(self, content: bytes, filename: str) -> bool:
        try:
            await self.initialize()
            doc_id = f"{filename}_{datetime.utcnow().isoformat()}"
            logger.info(f"Starting to index document {filename} with ID {doc_id}")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Load and process documents
                documents = SimpleDirectoryReader(input_dir=temp_dir).load_data()
                logger.info(f"Loaded {len(documents)} document chunks")
                
                # Process each document chunk
                for doc in documents:
                    # Generate embedding first
                    embedding = self.embed_model.get_text_embedding(doc.text)
                    
                    # Create document with metadata and embedding
                    doc.metadata = {
                        "filename": filename,
                        "active": True,
                        "doc_id": doc_id,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    # Store the embedding directly
                    await self.vector_store.client.index(
                        index="documents",
                        body={
                            "text": doc.text,
                            "metadata": doc.metadata,
                            "vector": embedding
                        }
                    )
                
                # Force refresh index
                await self.vector_store.client.indices.refresh(index="documents")
                logger.info(f"Successfully indexed document {filename}")
                return True
            
        except Exception as e:
            logger.error(f"Error indexing document {filename}: {str(e)}")
            logger.exception("Full error traceback:")
            raise

    async def query_index(self, question: str, max_results: int = 3) -> Dict[str, Any]:
        try:
            await self.initialize()
            query_embedding = self.embed_model.get_text_embedding(question)
            
            response = await self.vector_store.client.search(
                index="documents",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"metadata.active": True}}
                            ]
                        }
                    },
                    "knn": {
                        "field": "vector",
                        "query_vector": query_embedding,
                        "k": max_results,
                        "num_candidates": 100
                    },
                    "_source": ["text", "metadata"]
                }
            )
            
            return {
                "source_nodes": [
                    {
                        "text": hit["_source"]["text"],
                        "score": hit["_score"],
                        "filename": hit["_source"]["metadata"].get("filename", "Unknown")
                    } for hit in response["hits"]["hits"]
                ]
            }
        except Exception as e:
            logger.error(f"Error querying index: {str(e)}")
            raise

    async def get_documents(self) -> List[Dict[str, Any]]:
        try:
            await self.initialize()
            response = await self.vector_store.client.search(
                index="documents",
                body={
                    "query": {"match_all": {}},
                    "size": 1000,
                    "_source": ["metadata"],
                    "collapse": {
                        "field": "metadata.doc_id.keyword"
                    }
                }
            )
            
            return [
                {
                    "id": hit["_source"]["metadata"]["doc_id"],
                    "filename": hit["_source"]["metadata"]["filename"],
                    "active": hit["_source"]["metadata"]["active"]
                } for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            raise

    async def update_document_status(self, doc_id: str, active: bool) -> None:
        try:
            await self.initialize()
            await self.vector_store.client.update_by_query(
                index="documents",
                body={
                    "query": {"term": {"metadata.doc_id.keyword": doc_id}},
                    "script": {
                        "source": "ctx._source.metadata.active = params.active",
                        "params": {"active": active}
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            raise 

    async def clear_all_data(self) -> None:
        try:
            await self.initialize()
            await self.vector_store.client.delete_by_query(
                index="documents",
                body={
                    "query": {"match_all": {}}
                },
                refresh=True
            )
            logger.info("Successfully cleared all data")
        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            raise 

    async def inspect_index(self) -> None:
        """Debug method to inspect index contents"""
        try:
            await self.initialize()
            response = await self.vector_store.client.search(
                index="documents",
                body={
                    "query": {"match_all": {}},
                    "size": 1,
                    "_source": True
                }
            )
            if response["hits"]["hits"]:
                doc = response["hits"]["hits"][0]["_source"]
                logger.info(f"Sample document structure: {doc.keys()}")
                logger.info(f"Metadata structure: {doc.get('metadata', {}).keys()}")
                logger.info(f"Has vector: {'vector' in doc}")
                logger.info(f"Vector dimension: {len(doc.get('vector', []))}")
        except Exception as e:
            logger.error(f"Error inspecting index: {str(e)}") 