from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
    StorageContext
)
from llama_index.core.node_parser import SimpleNodeParser, SentenceSplitter
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from app.utils.weaviate_client import create_vector_store
from app.utils.logger import setup_logger
from app.utils.document_utils import extract_text_from_pdf, extract_text_from_docx
import uuid
from typing import List, Dict, Any, Optional
import backoff
from llama_index.core.vector_stores import VectorStoreQuery, MetadataFilters, ExactMatchFilter
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from weaviate.classes.query import Filter

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
        # Get pre-configured vector store
        self.vector_store = await create_vector_store()
        
        # Create storage context and index
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = VectorStoreIndex([], storage_context=storage_context)

    async def index_document(self, content: bytes, filename: str) -> None:
        try:
            # Handle different file types
            if filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(content)
            elif filename.lower().endswith('.docx'):
                text = extract_text_from_docx(content)
            else:
                text = content.decode('utf-8')

            doc_id = str(uuid.uuid4())
            chunks = chunk_text(text)
            
            # Create TextNode objects with metadata
            nodes = [
                TextNode(
                    text=chunk,
                    metadata={
                        "filename": filename,
                        "doc_id": doc_id,
                        "chunk_id": i,
                        "active": True
                    },
                    embedding=self.embed_model.get_text_embedding(chunk)
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Use vector store's add method
            self.vector_store.add(nodes)
            
            logger.info(f"Indexed {len(chunks)} chunks for {filename}")
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise

    async def query_index(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        try:
            query_embedding = self.embed_model.get_text_embedding(query)
            
            # Use vector store's query method
            query_result = self.vector_store.query(
                VectorStoreQuery(
                    query_embedding=query_embedding,
                    similarity_top_k=max_results,
                    filters=MetadataFilters(filters=[
                        ExactMatchFilter(key="active", value="true")
                    ])
                )
            )
            
            return {
                "results": [
                    {
                        "text": node.text,
                        "metadata": node.metadata,
                        "score": score
                    } for node, score in zip(query_result.nodes, query_result.similarities)
                ]
            }
        except Exception as e:
            logger.error(f"Query index error: {str(e)}")
            raise

    async def get_documents(self) -> List[Dict[str, Any]]:
        """Get list of all documents with their status"""
        try:
            # Get all document IDs using vector store's metadata filter
            query_result = self.vector_store.query(
                VectorStoreQuery(
                    query_embedding=None,
                    similarity_top_k=1000,
                    filters=MetadataFilters(filters=[
                        ExactMatchFilter(key="active", value="true")
                    ])
                )
            )
            
            # Group by doc_id to get unique documents
            documents = {}
            for node in query_result.nodes:
                doc_id = node.metadata.get("doc_id")
                if doc_id and doc_id not in documents:
                    documents[doc_id] = {
                        "id": doc_id,
                        "filename": node.metadata.get("filename"),
                        "active": node.metadata.get("active", True)
                    }
            
            return list(documents.values())
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            raise

    async def delete_document(self, doc_id: str) -> None:
        """Delete a specific document and all its chunks"""
        try:
            # Correct deletion using official API
            self.vector_store.delete(
                ref_doc_id=doc_id,
                filters=MetadataFilters(filters=[
                    ExactMatchFilter(key="doc_id", value=doc_id)
                ])
            )
            logger.info(f"Deleted document {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    async def clear_all_data(self) -> None:
        """Delete all documents from the vector store"""
        try:
            # Use built-in clear method
            self.vector_store.clear()
            logger.info("All documents deleted")
        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            raise

    async def update_document_status(self, doc_id: str, active: bool) -> None:
        """Update the active status of a document"""
        try:
            # Correct update using WeaviateVectorStore's data operations
            collection = self.vector_store.client.collections.get("Documents")
            result = collection.data.update_many(
                where=Filter.by_property("doc_id").equal(doc_id),
                properties={"active": "true"} if active else {"active": "false"}
            )
            logger.info(f"Updated {result} documents for {doc_id}")
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            raise

    async def query(self, question: str, top_k: int = 5, hybrid: bool = False):
        try:
            query_embedding = self.embed_model.get_text_embedding(question)
            
            # Use vector store's query method
            query_result = self.vector_store.query(
                query=VectorStoreQuery(
                    query_embedding=query_embedding,
                    similarity_top_k=top_k,
                    mode=VectorStoreQueryMode.HYBRID if hybrid else VectorStoreQueryMode.DEFAULT,
                    alpha=0.5 if hybrid else None,
                    filters=MetadataFilters(filters=[
                        ExactMatchFilter(key="active", value="true")
                    ])
                )
            )
            
            # Process results
            results = []
            for node, score in zip(query_result.nodes, query_result.similarities):
                results.append({
                    "text": node.text,
                    "filename": node.metadata.get("filename", "unknown"),
                    "similarity_score": score,
                    "doc_id": node.metadata.get("doc_id")
                })
            
            logger.info(f"Found {len(results)} relevant documents for query '{question}'")
            return results
            
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