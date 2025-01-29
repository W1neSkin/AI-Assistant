from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
)
from llama_index.core.node_parser import SimpleNodeParser, SentenceSplitter
from llama_index.core.schema import QueryBundle
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file.docs import PDFReader, DocxReader
from app.utils.weaviate_client import create_vector_store
from app.utils.logger import setup_logger
from app.utils.document_utils import extract_text_from_pdf, extract_text_from_docx
import uuid
from typing import List, Dict, Any, Optional
import tempfile
import os
import backoff
import json
import time

logger = setup_logger(__name__)

@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3,
    max_time=30
)
def create_embedding_model():
    return HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en",
        cache_folder="/app/storage/models/embeddings"
    )

class LlamaIndexService:
    def __init__(self):
        self.vector_store = None
        self.index = None
        # The embedding model is used here to convert document text into vectors
        self.embed_model = create_embedding_model()
        self.node_parser = SimpleNodeParser.from_defaults()
        Settings.embed_model = self.embed_model
        Settings.node_parser = self.node_parser

    async def initialize(self):
        self.vector_store = await create_vector_store()
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store
        )

    async def index_document(self, content: bytes, filename: str) -> None:
        try:
            # Handle different file types
            if filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(content)
            elif filename.lower().endswith('.docx'):
                text = extract_text_from_docx(content)
            else:
                text = content.decode('utf-8')


            # Proceed with indexing the extracted text
            doc_id = str(uuid.uuid4())
            chunks = chunk_text(text)
            
            # Configure batch with retry logic
            self.vector_store.client.batch.configure(
                batch_size=50,  # Optimal for most setups
                dynamic=True,
                timeout_retries=3,
                callback=handle_batch_errors
            )

            with self.vector_store.client.batch as batch:
                for i, chunk in enumerate(chunks):
                    vector = self.embed_model.get_text_embedding(chunk)
                    data_object = {
                        "text": chunk,
                        "filename": filename,
                        "doc_id": doc_id,
                        "chunk_id": i,
                        "active": True
                    }
                    batch.add_data_object(
                        data_object=data_object,
                        class_name="Documents",
                        vector=vector
                    )
                    # Add pause every 100 chunks
                    if i % 100 == 0:
                        time.sleep(0.1)
            
            logger.info(f"Indexed {len(chunks)} chunks for {filename}")
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise

    async def query_index(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        try:
            # Get query embedding
            query_embedding = self.embed_model.get_text_embedding(query)

            # Search in Weaviate with vector
            result = (
                self.vector_store.client.collections.get("Documents")
                .with_near_vector({
                    "vector": query_embedding
                })
                .with_limit(max_results)
                .with_additional(["score"])  # Fetch additional metadata
                .do()  # Use do() to execute the query
            )

            # Process results
            results = []
            for item in result.get("data", {}).get("Get", {}).get("Documents", []):
                results.append({
                    "text": item.get("text", ""),
                    "filename": item.get("metadata", {}).get("filename", "unknown"),
                    "similarity_score": item.get("_additional", {}).get("score", 0),
                    "doc_id": item.get("metadata", {}).get("doc_id")
                })

            logger.info(f"Found {len(results)} relevant documents for query '{query}'")
            return results

        except Exception as e:
            logger.error(f"Error performing semantic search for query '{query}': {str(e)}")
            raise

    
    async def get_documents(self) -> List[Dict[str, Any]]:
        """Get list of all documents with their status"""
        try:
            if not self.vector_store:
                await self.initialize()
            
            # Query all unique documents from Weaviate
            result = (
                self.vector_store.client.collections.get("Documents")
                .do()  # Use do() to execute the query
            )
            
            # Group by doc_id to get unique documents
            documents = {}
            for item in result.get("data", {}).get("Get", {}).get("Documents", []):
                metadata = item.get("metadata", {})
                doc_id = metadata.get("doc_id")
                
                if doc_id and doc_id not in documents:
                    documents[doc_id] = {
                        "id": doc_id,
                        "filename": metadata.get("filename"),
                        "active": metadata.get("active", True)
                    }
            
            logger.info(f"Found {len(documents)} documents")
            return list(documents.values())
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            raise

    async def delete_document(self, doc_id: str) -> None:
        """Delete a specific document and all its chunks"""
        try:
            if not self.vector_store:
                await self.initialize()
            
            # Delete all objects with matching doc_id
            result = self.vector_store.client.collections.delete(
                name="Documents",
                where={
                    "path": ["metadata", "doc_id"],
                    "operator": "Equal",
                    "valueString": doc_id
                }
            )
            
            if result is True:
                logger.info(f"Document deleted successfully: {doc_id}")
            else:
                logger.warning(f"Document deletion may have failed: {doc_id}")
                
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            raise

    async def clear_all_data(self) -> None:
        """Delete all documents from the vector store"""
        try:
            if not self.vector_store:
                await self.initialize()
            
            # Delete all objects in the Documents class
            self.vector_store.client.schema.delete_class("Documents")
            
            # Recreate the schema
            await create_vector_store()
            
            logger.info("All documents deleted successfully")
        except Exception as e:
            logger.error(f"Error clearing all documents: {str(e)}")
            raise

    async def update_document_status(self, doc_id: str, active: bool) -> None:
        """Update the active status of a document"""
        try:
            if not self.vector_store:
                await self.initialize()
            
            # Update all chunks of the document
            result = self.vector_store.client.collections.update(
                name="Documents",
                where={
                    "path": ["metadata", "doc_id"],
                    "operator": "Equal",
                    "valueString": doc_id
                },
                properties={
                    "metadata": {
                        "active": active
                    }
                }
            )
            
            if result is True:
                logger.info(f"Document status updated successfully: {doc_id} -> {active}")
            else:
                logger.warning(f"Document status update may have failed: {doc_id}")
                
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            raise

    async def query(self, question: str, top_k: int = 5):
        try:
            query_embedding = self.embed_model.get_text_embedding(question)
            
            result = (
                self.vector_store.client.query
                .get("Documents", ["text", "filename", "doc_id"])
                .with_near_vector({
                    "vector": query_embedding,
                    "distance": 0.2  # More precise than certainty
                })
                .with_where({
                    "path": ["active"],
                    "operator": "Equal",
                    "valueBoolean": True
                })
                .with_limit(top_k)
                .with_additional(["distance"])
                .do()
            )
            
            # Add score normalization
            max_distance = max([item["_additional"]["distance"] for item in result["data"]["Get"]["Documents"]], default=1)
            return [{
                **item,
                "similarity_score": 1 - (item["_additional"]["distance"] / max_distance) if max_distance != 0 else 0
            } for item in result["data"]["Get"]["Documents"]]
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            raise 

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """Split text into chunks with overlap using proper text splitting"""
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separator=" ",
        paragraph_separator="\n\n",
        secondary_chunking_regex="[^,.;。]+[,.;。]?",
    )
    return [node.text for node in splitter.get_nodes_from_documents([Document(text=text)])] 

def handle_batch_errors(results: Optional[list]) -> None:
    if not results:
        return
    for result in results:
        if "errors" in result:
            logger.error(f"Batch error: {result['errors']}")
            raise Exception("Batch operation failed") 