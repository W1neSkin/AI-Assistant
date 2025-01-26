from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import QueryBundle
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file.docs import PDFReader, DocxReader
from app.utils.es_client import create_vector_store
from app.utils.logger import setup_logger
import uuid
from typing import List, Dict, Any
import tempfile
import os
import backoff
import json

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
            doc_id = str(uuid.uuid4())
            logger.debug(f"Processing document: {filename}")
            
            # Function to chunk text
            def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
                sentences = text.split('. ')
                chunks = []
                current_chunk = []
                current_size = 0
                
                for sentence in sentences:
                    sentence = sentence.strip() + '. '
                    if current_size + len(sentence) > chunk_size and current_chunk:
                        chunks.append(''.join(current_chunk))
                        current_chunk = [sentence]
                        current_size = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_size += len(sentence)
                
                if current_chunk:
                    chunks.append(''.join(current_chunk))
                return chunks

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
            
            logger.debug(f"Document content length: {len(text)}")
            logger.debug(f"First 200 chars: {text[:200]}")
            
            # Split text into chunks and index each chunk
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                vector = self.embed_model.get_text_embedding(chunk)
                await self.vector_store.client.index(
                    index="documents",
                    id=chunk_id,
                    body={
                        "text": chunk,
                        "vector": vector,
                        "metadata": {
                            'filename': filename,
                            'doc_id': doc_id,
                            'chunk_id': i,
                            'active': True
                        }
                    }
                )
            
            # Force refresh to make document immediately available
            await self.vector_store.client.indices.refresh(index="documents")
            
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
            # Refresh index to ensure we get latest data
            await self.vector_store.client.indices.refresh(index="documents")
            
            response = await self.vector_store.client.search(
                index="documents",
                body={
                    "query": {"match_all": {}},
                    "size": 1000,
                    "track_total_hits": True,
                    "sort": [{"metadata.filename.keyword": {"order": "asc"}}],
                    "_source": ["metadata"]
                }
            )
            
            logger.info(f"Found {response['hits']['total']['value']} total documents")
            
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
            
            logger.debug(f"Returning {len(documents)} unique documents")
            return list(documents.values())
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            raise

    async def delete_document(self, doc_id: str) -> None:
        try:
            logger.info(f"Attempting to delete document with ID: {doc_id}")
            
            # Delete from Elasticsearch index
            await self.vector_store.client.delete_by_query(
                index="documents",
                body={
                    "query": {
                        "term": {
                            "metadata.doc_id": doc_id
                        }
                    }
                }
            )
            
            # Force refresh to make the deletion visible immediately
            await self.vector_store.client.indices.refresh(index="documents")
            
            # Verify deletion
            result = await self.vector_store.client.search(
                index="documents",
                body={
                    "query": {
                        "term": {
                            "metadata.doc_id": doc_id
                        }
                    }
                }
            )
            
            if result["hits"]["total"]["value"] > 0:
                raise Exception("Document still exists after deletion")
            
            logger.info(f"Document deleted successfully: {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
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

    async def query(self, question: str, top_k: int = 5):
        """
        Query documents using semantic search
        Args:
            question: User's question text
            top_k: Number of most relevant documents to retrieve
        """
        try:
            if not self.vector_store:
                await self.initialize()
            
            query_embedding = self.embed_model.get_text_embedding(question)
            
            # First, get candidate documents using KNN
            response = await self.vector_store.client.search(
                index="documents",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "bool": {
                                        "should": [
                                            # Vector similarity
                                            {
                                                "script_score": {
                                                    "query": {"match_all": {}},
                                                    "script": {
                                                        "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                                                        "params": {"query_vector": query_embedding}
                                                    }
                                                }
                                            },
                                            # Text matching
                                            {
                                                "multi_match": {
                                                    "query": question,
                                                    "fields": ["text^3", "text._2gram", "text._3gram"],
                                                    "type": "most_fields",
                                                    "operator": "or",
                                                    "minimum_should_match": "30%"
                                                }
                                            }
                                        ]
                                    }
                                }
                            ],
                            "filter": [
                                {
                                    "term": {
                                        "metadata.active": True
                                    }
                                }
                            ]
                        }
                    },
                    "min_score": 0.3,  # Filter out low-quality matches
                    "_source": True,
                    "size": top_k * 2  # Get more candidates initially
                }
            )
            
            # Process and format results
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                text = source.get("text", source.get("node", {}).get("text", ""))
                metadata = source.get("metadata", source.get("node", {}).get("metadata", {}))
                
                if not text.strip():
                    continue
                
                # Calculate combined relevance score
                vector_score = float(hit["_score"]) - 1.0  # Normalize cosine similarity to [0,1]
                text_match_score = len(set(question.lower().split()) & set(text.lower().split())) / len(set(question.lower().split()))
                combined_score = (vector_score * 0.7) + (text_match_score * 0.3)  # Weight vector similarity higher
                
                results.append({
                    'text': text,
                    'filename': metadata.get('filename', 'unknown'),
                    'similarity_score': combined_score,
                    'doc_id': metadata.get('doc_id')
                })
            
            # Sort by combined score and take top_k
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = results[:top_k]
            
            logger.info(f"Found {len(results)} relevant documents for query: {question[:100]}...")
            for result in results:
                logger.debug(f"Document: {result['filename']}, Score: {result['similarity_score']}")
                logger.debug(f"Text snippet: {result['text'][:200]}...")
            
            # Create query bundle with context
            context_texts = [doc['text'] for doc in results if doc['text'].strip()]
            query_bundle = QueryBundle(
                query_str=question,
                custom_embedding_strs=context_texts
            )
            
            return query_bundle, results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            raise 