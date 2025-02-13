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
from llama_index.core.vector_stores import VectorStoreQuery, MetadataFilters, MetadataFilter, ExactMatchFilter
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from weaviate.classes.query import Filter
import hashlib

logger = setup_logger(__name__)

@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3,
    max_time=30
)
def create_embedding_model():
    logger.info("Creating embedding model...")
    model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en",
        cache_folder="/app/storage/models/embeddings"
    )
    logger.info("Embedding model created successfully")
    return model


class LlamaIndexService:
    def __init__(self):
        logger.info("Initializing LlamaIndexService...")
        self.vector_store = None
        self.index = None
        logger.info("Creating embedding model instance...")
        self.embed_model = create_embedding_model()
        logger.debug(f"Embedding model created: {self.embed_model}")
        
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=512,
            chunk_overlap=50
        )
        Settings.embed_model = self.embed_model
        Settings.node_parser = self.node_parser
        logger.info("LlamaIndexService initialization complete")

    async def initialize(self):
        # Get pre-configured vector store
        self.vector_store = await create_vector_store()
        
        # Create storage context and index
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = VectorStoreIndex([], storage_context=storage_context)

    async def index_document(self, content: bytes, filename: str, user_id: str):
        """Index document with chunking and user tracking"""
        try:
            # Generate document ID
            file_size = len(content)
            doc_id = self._generate_doc_id(filename, file_size)
            
            # Check if document exists
            existing_doc = await self._get_document_by_id(doc_id)
            if existing_doc:
                # Just add user to the users list if document exists
                await self._add_user_to_document(doc_id, user_id)
                return doc_id
            
            # Extract text from content
            text = self._extract_text(content, filename)
            
            # Create document and split into chunks
            doc = Document(text=text)
            nodes = self.node_parser.get_nodes_from_documents([doc])
            
            # Add metadata to each chunk
            total_chunks = len(nodes)
            for i, node in enumerate(nodes):
                node.metadata.update({
                    "doc_id": doc_id,
                    "search_id": doc_id,
                    "filename": filename,
                    "chunk_id": i,
                    "total_chunks": total_chunks,
                    "file_size": file_size,
                    "users": [user_id],
                    "active": "true"
                })
            
            # Index all chunks
            await self._add_nodes(nodes)
            return doc_id
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise

    async def query(self, question: str, user_id: str, max_results: int = 5, hybrid: bool = False) -> List[Dict]:
        """Query documents with user filter"""
        try:
            query_embedding = self.embed_model.get_text_embedding(question)
            
            # Add filters for active documents and user access
            filters = MetadataFilters(filters=[
                ExactMatchFilter(key="active", value="true"),
                MetadataFilter(key="users", value=[user_id], operator="any"),
            ])
            
            # Query vector store
            query_result = self.vector_store.query(
                VectorStoreQuery(
                    query_embedding=query_embedding,
                    similarity_top_k=max_results,
                    mode=VectorStoreQueryMode.HYBRID if hybrid else VectorStoreQueryMode.DEFAULT,
                    alpha=0.5 if hybrid else None,
                    filters=filters
                )
            )
            
            # Process results
            results = []
            seen_docs = set()
            for node, score in zip(query_result.nodes, query_result.similarities):
                doc_id = node.metadata.get("doc_id")
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    results.append({
                        "text": node.text,
                        "filename": node.metadata.get("filename", "unknown"),
                        "similarity_score": score,
                        "chunk_id": node.metadata.get("chunk_id"),
                        "total_chunks": node.metadata.get("total_chunks")
                    })
            
            logger.info(f"Found {len(results)} relevant documents for query '{question}'")
            return results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            raise

    async def delete_document(self, doc_id: str, user_id: str):
        """Remove document from user's list"""
        doc = await self._get_document_by_id(doc_id)
        if not doc:
            return
            
        users = doc.get("users", [])
        if user_id in users:
            users.remove(user_id)
            
            if not users:
                # No users left, delete document completely
                await self._delete_document(doc_id)
            else:
                # Update users list
                await self._update_document_users(doc_id, users)

    async def get_user_documents(self, user_id: str) -> List[Dict]:
        """Get list of user's documents"""
        try:
        # Query using MetadataFilters directly
            logger.debug(f"Querying documents for user {user_id} {type(user_id)}")
            
            # Add filters for active documents and user access
            filters = MetadataFilters(filters=[
                MetadataFilter(key="users", value=[user_id], operator="any"),
            ])

            query_result = self.vector_store.query(
                VectorStoreQuery(
                    query_embedding=None,  # No embedding needed for listing
                    similarity_top_k=1000,  # Get all matching documents
                    filters=filters
                )
            )
            
            # Process results
            documents = []
            seen_docs = set()
         
            for node in query_result.nodes:
                doc_id = node.metadata.get("doc_id")
                if doc_id and doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    documents.append({
                        "id": doc_id,
                        "filename": node.metadata.get("filename", "unknown"),
                        "size": node.metadata.get("file_size", 0),
                        "active": node.metadata.get("active", "true") == "true"
                    })
            
            return documents
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            raise

    async def update_document_status(self, doc_id: str, active: bool) -> None:
        """Update the active status of a document"""
        try:
            # Get all nodes for this document
            filters=MetadataFilters(filters=[
                        MetadataFilter(key="search_id", value=doc_id),
                    ])
            
            query_result = self.vector_store.query(
                VectorStoreQuery(
                    query_embedding=None,
                    similarity_top_k=1000,
                    filters=filters
                )
            )
            
            # Update active status in metadata
            for node in query_result.nodes:
                node.metadata["active"] = "true" if active else "false"
            
            logger.debug(f"Updated nodes: {query_result.nodes}")
            # Update nodes in vector store
            if query_result.nodes:
                # Delete old nodes and add updated ones
                self.vector_store.delete(ref_doc_id=doc_id)
                self.vector_store.add(
                    nodes=query_result.nodes,
                )
            
            logger.info(f"Updated document status for {doc_id}")
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            raise

    async def clear_user_documents(self, user_id: str) -> None:
        """Delete all documents for specific user"""
        try:
            # Get all documents for user
            docs = await self.get_user_documents(user_id)
            
            # Remove user from each document
            for doc in docs:
                await self.delete_document(doc["id"], user_id)
                
            logger.info(f"Cleared all documents for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing user documents: {str(e)}")
            raise

    async def _get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID"""
        try:
            # Query for document with specific doc_id
            query_result = self.vector_store.query(
                VectorStoreQuery(
                    query_embedding=None,  # No embedding needed for exact match
                    filters=MetadataFilters(filters=[
                        ExactMatchFilter(key="search_id", value=doc_id)
                    ]),
                    similarity_top_k=1  # We only need one result
                )
            )
            
            if query_result.nodes:
                node = query_result.nodes[0]
                return {
                    "doc_id": node.metadata.get("doc_id"),
                    "filename": node.metadata.get("filename"),
                    "file_size": node.metadata.get("file_size"),
                    "users": node.metadata.get("users", [])
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            raise

    async def _add_nodes(self, nodes: List[TextNode]) -> None:
        """Add nodes to vector store"""
        try:
            for node in nodes:
                node.embedding = self.embed_model.get_text_embedding(node.text)

            self.vector_store.add(nodes=nodes)
            logger.info(f"Added {len(nodes)} nodes to vector store")
        except Exception as e:
            logger.error(f"Error adding nodes: {str(e)}")
            raise

    async def _add_user_to_document(self, doc_id: str, user_id: str) -> None:
        """Add user to document's users list"""
        try:
            # Get current document nodes
            query_result = self.vector_store.query(
                VectorStoreQuery(
                    query_embedding=None,
                    filters=MetadataFilters(filters=[
                        ExactMatchFilter(key="search_id", value=doc_id)
                    ])
                )
            )
            
            if not query_result.nodes:
                raise ValueError(f"Document {doc_id} not found")
            
            # Update users list in metadata
            for node in query_result.nodes:
                users = node.metadata.get("users", [])
                if user_id not in users:
                    users.append(user_id)
                    node.metadata["users"] = users
            
            # Delete old nodes and add updated ones
            self.vector_store.delete(
                filter=MetadataFilters(filters=[
                    ExactMatchFilter(key="search_id", value=doc_id)
                ])
            )
            self.vector_store.add(nodes=query_result.nodes)
            
            logger.info(f"Added user {user_id} to document {doc_id}")
            
        except Exception as e:
            logger.error(f"Error adding user to document: {str(e)}")
            raise

    def _extract_text(self, content: bytes, filename: str) -> str:
        """Extract text based on file type"""
        if filename.lower().endswith('.pdf'):
            return extract_text_from_pdf(content)
        elif filename.lower().endswith('.docx'):
            return extract_text_from_docx(content)
        else:
            return content.decode('utf-8')
        
    def _generate_doc_id(self, filename: str, file_size: int) -> str:
        """Generate unique document ID based on filename and size"""
        unique_str = f"{filename}:{file_size}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    