from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.storage import StorageContext
from llama_index.core.settings import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from utils.es_client import create_vector_store
from utils.logger import setup_logger
from typing import Dict, Any
import tempfile
import os
import gc
import torch

logger = setup_logger(__name__)

class LlamaIndexService:
    def __init__(self):
        logger.info("Initializing LlamaIndexService...")
        self.vector_store = None
        self.storage_context = None
        # Use a smaller, more memory-efficient model
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",
            embed_batch_size=4
        )
        
        # Initialize settings with only embeddings, no LLM
        Settings.embed_model = self.embed_model
        Settings.llm = None  # Explicitly set LLM to None

    async def initialize(self):
        """Initialize async components"""
        if self.vector_store is None:
            self.vector_store = await create_vector_store()
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            logger.info("LlamaIndexService initialized successfully")

    def _clear_memory(self):
        """Clear memory after heavy operations"""
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

    async def index_document(self, content: bytes, filename: str) -> bool:
        try:
            await self.initialize()
            logger.info(f"Starting to index document: {filename}")
            
            # Create a temporary directory to store the file
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, filename)
                
                # Write the content to a temporary file
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Use SimpleDirectoryReader to handle different file types
                documents = SimpleDirectoryReader(
                    input_dir=temp_dir,
                    filename_as_id=True
                ).load_data()
                
                # Process documents in smaller chunks if needed
                chunk_size = 10
                for i in range(0, len(documents), chunk_size):
                    chunk = documents[i:i + chunk_size]
                    # Index the documents
                    index = VectorStoreIndex.from_documents(
                        chunk,
                        storage_context=self.storage_context,
                        show_progress=True
                    )
                    # Clear memory after each chunk
                    self._clear_memory()
                
                # Force index refresh
                await self.vector_store.client.indices.refresh(index="documents")
                
                logger.info(f"Successfully indexed document: {filename}")
                return True
        except Exception as e:
            logger.error(f"Error indexing document {filename}: {str(e)}")
            raise 
        finally:
            self._clear_memory()

    async def query_index(self, question: str, max_results: int = 3) -> Dict[str, Any]:
        try:
            await self.initialize()
            logger.info(f"Processing query: {question}")
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store
            )
            
            # Create a retriever that only fetches relevant documents
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=max_results
            )
            
            # Create a query engine that only retrieves, doesn't generate
            query_engine = RetrieverQueryEngine(
                retriever=retriever
            )
            
            response = query_engine.query(question)
            logger.info("Query processed successfully")
            
            return {
                "source_nodes": [
                    {
                        "text": node.node.text,
                        "score": node.score,
                        "document_id": node.node.doc_id if hasattr(node.node, 'doc_id') else None
                    } for node in response.source_nodes
                ]
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
        finally:
            self._clear_memory() 

    async def clear_all_data(self):
        """Clear all indexed documents from Elasticsearch"""
        try:
            await self.initialize()
            logger.info("Clearing all data from vector store")
            
            # Delete all documents from the index using Elasticsearch client
            await self.vector_store.client.delete_by_query(
                index="documents",
                body={
                    "query": {
                        "match_all": {}
                    }
                },
                refresh=True
            )
            
            logger.info("Successfully cleared all data")
        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            raise 