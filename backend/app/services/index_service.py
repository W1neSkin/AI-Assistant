from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file.docs import PDFReader, DocxReader
from app.utils.es_client import create_vector_store
from app.utils.logger import setup_logger
import uuid
from typing import List, Dict, Any
import tempfile
import os
import time
import backoff

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
        cache_folder="./models/embeddings"
    )

class LlamaIndexService:
    def __init__(self):
        try:
            self.embed_model = create_embedding_model()
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing embedding model: {str(e)}")
            raise
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
            doc_id = str(uuid.uuid4())
            # Handle different file types
            if filename.lower().endswith('.pdf'):
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                try:
                    reader = PDFReader()
                    documents = reader.load_data(temp_path)
                    text = "\n".join(doc.text for doc in documents)
                finally:
                    # Clean up temp file
                    os.unlink(temp_path)
            elif filename.lower().endswith('.docx'):
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                try:
                    reader = DocxReader()
                    documents = reader.load_data(temp_path)
                    text = "\n".join(doc.text for doc in documents)
                finally:
                    os.unlink(temp_path)
            else:
                # Try different encodings for text files
                encodings = ['utf-8', 'latin1', 'cp1252']
                text = None
                for encoding in encodings:
                    try:
                        text = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                if text is None:
                    raise ValueError(f"Could not decode file {filename} with any supported encoding")
            
            document = Document(
                text=text,
                metadata={
                    'filename': filename,
                    'doc_id': doc_id,
                    'active': True
                }
            )
            self.index.insert(document)
            logger.info(f"Document indexed successfully: {filename}")
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise

    async def query_index(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        try:
            retriever = self.index.as_retriever(similarity_top_k=max_results)
            nodes = retriever.retrieve(query)
            
            return {
                "source_nodes": [
                    {
                        "text": node.text,
                        "score": node.score if hasattr(node, 'score') else None,
                        "filename": node.metadata.get('filename', 'Unknown') if node.metadata else 'Unknown'
                    }
                    for node in nodes
                ]
            }
        except Exception as e:
            logger.error(f"Error querying index: {str(e)}")
            raise

    async def clear_all_data(self) -> None:
        try:
            await self.vector_store.delete(delete_all=True)
            logger.info("All data cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            raise

    async def get_documents(self) -> List[Dict[str, Any]]:
        try:
            response = await self.vector_store.client.search(
                index="documents",
                body={
                    "query": {"match_all": {}},
                    "size": 1000,
                    "sort": [{"metadata.filename.keyword": {"order": "asc"}}],
                    "_source": ["metadata"]
                }
            )
            
            documents = {}
            for hit in response["hits"]["hits"]:
                metadata = hit["_source"]["metadata"]
                doc_id = metadata.get("doc_id")
                
                if doc_id not in documents:
                    documents[doc_id] = {
                        "id": doc_id,
                        "filename": metadata.get("filename"),
                        "active": metadata.get("active", True)
                    }
            
            return list(documents.values())
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            raise

    async def delete_document(self, doc_id: str) -> None:
        try:
            await self.vector_store.client.delete_by_query(
                index="documents",
                body={
                    "query": {
                        "term": {
                            "metadata.doc_id.keyword": doc_id
                        }
                    }
                }
            )
            logger.info(f"Document deleted successfully: {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    async def update_document_status(self, doc_id: str, active: bool) -> None:
        try:
            await self.vector_store.client.update_by_query(
                index="documents",
                body={
                    "script": {
                        "source": "ctx._source.metadata.active = params.active",
                        "params": {"active": active}
                    },
                    "query": {
                        "term": {
                            "metadata.doc_id.keyword": doc_id
                        }
                    }
                }
            )
            logger.info(f"Document status updated successfully: {doc_id} -> {active}")
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            raise 