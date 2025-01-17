from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    Settings,
    StorageContext,
    Document
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from utils.es_client import create_vector_store
from utils.logger import setup_logger
from typing import Dict, Any, List
import tempfile
import os
from datetime import datetime
from bs4 import BeautifulSoup
from llama_cpp import Llama

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
                
                # Choose reader based on file extension
                if filename.lower().endswith('.html'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        # Get text and create document
                        text = soup.get_text(separator='\n', strip=True)
                        documents = [Document(text=text)]
                else:
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

    async def delete_document(self, doc_id: str) -> None:
        """Delete a document and its chunks from the index"""
        try:
            await self.initialize()
            # Delete all chunks with matching doc_id
            await self.vector_store.client.delete_by_query(
                index="documents",
                body={
                    "query": {
                        "term": {
                            "metadata.doc_id.keyword": doc_id
                        }
                    }
                },
                refresh=True
            )
            logger.info(f"Successfully deleted document {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            logger.exception("Full error traceback:")
            raise 

class LocalLLM:
    def __init__(self, model_path: str):
        self.model = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4,
            n_batch=512,
            verbose=True,
            f16_kv=True
        )
        
    def estimate_tokens(self, text: str) -> int:
        # More conservative token estimation
        return int(len(text.encode('utf-8')) / 3)  # Rough byte-to-token ratio
        
    def truncate_context(self, context: str, max_tokens: int) -> str:
        # Split into sentences for more natural truncation
        sentences = context.split('. ')
        truncated = []
        current_tokens = 0
        
        for sentence in sentences:
            tokens = self.estimate_tokens(sentence)
            if current_tokens + tokens > max_tokens:
                break
            truncated.append(sentence)
            current_tokens += tokens
        
        return '. '.join(truncated)
        
    async def generate_answer(self, prompt: str) -> str:
        # Detect if query is in Russian
        is_russian = any(ord(char) >= 1040 and ord(char) <= 1103 for char in prompt)
        
        # Extract question and context
        question_start = prompt.find("answer the question:") + 19
        context_start = prompt.find("Context:") + 8
        
        question = prompt[question_start:context_start].strip()
        context = prompt[context_start:].strip()
        
        # Calculate available tokens for context
        instruction_tokens = 300  # Increased for safety
        question_tokens = self.estimate_tokens(question)
        response_tokens = 512  # Reserved for response
        available_tokens = 2500  # More conservative limit for context
        
        # Truncate context if needed
        if self.estimate_tokens(context) > available_tokens:
            context = self.truncate_context(context, available_tokens)
        
        # Format prompt based on language
        if is_russian:
            formatted_prompt = (
                "<s>[INST] Ты русскоязычный ассистент. "
                "Твоя задача - отвечать ТОЛЬКО на русском языке. "
                "Посторайся использовать ТОЛЬКО информацию из предоставленного контекста. "
                "Если в контексте недостаточно информации, ответь: "
                "\"Извините, в предоставленном контексте недостаточно информации для ответа на этот вопрос.\"\n\n"
                f"Вопрос: {question}\n\nКонтекст: {context} [/INST]</s>"
            )
        else:
            formatted_prompt = (
                "<s>[INST] You are a helpful assistant. "
                "Please provide a detailed answer based on the given context. "
                "Answer should be factual and based only on the provided context.\n\n"
                f"Question: {question}\n\nContext: {context} [/INST]</s>"
            )

        try:
            response = self.model.create_completion(
                prompt=formatted_prompt,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                stop=["</s>", "[INST]", "Human:", "Assistant:"],
                echo=False
            )
            
            answer = response['choices'][0]['text'].strip()
            
            # For Russian queries, ensure answer is in Russian
            if is_russian and not any(ord(char) >= 1040 and ord(char) <= 1103 for char in answer):
                logger.warning("Answer not in Russian, forcing translation")
                translation_prompt = (
                    "[INST] Переведи следующий текст на русский язык, "
                    "сохраняя всю фактическую информацию:\n\n"
                    f"{answer} [/INST]"
                )
                
                response = self.model.create_completion(
                    prompt=translation_prompt,
                    max_tokens=512,
                    temperature=0.3,  # Lower temperature for translation
                    stop=["</s>", "[INST]"],
                    echo=False
                )
                answer = response['choices'][0]['text'].strip()
            
            return answer
            
        except ValueError as e:
            if "exceed context window" in str(e):
                # Fallback with even shorter context
                context_start = formatted_prompt.find("\n\n") + 2
                context = formatted_prompt[context_start:-7]
                words = context.split()
                truncated_words = words[:1500]
                truncated_context = ' '.join(truncated_words)
                formatted_prompt = formatted_prompt[:context_start] + truncated_context + " [/INST]"
                
                response = self.model.create_completion(
                    prompt=formatted_prompt,
                    max_tokens=512,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    stop=["</s>", "[INST]"],
                    echo=False
                )
                
                answer = response['choices'][0]['text'].strip()
                
                # Check for Russian translation need in fallback case too
                if is_russian and not any(ord(char) >= 1040 and ord(char) <= 1103 for char in answer):
                    translation_prompt = (
                        "[INST] Переведи следующий текст на русский язык:\n\n"
                        f"{answer} [/INST]"
                    )
                    response = self.model.create_completion(
                        prompt=translation_prompt,
                        max_tokens=512,
                        temperature=0.3,
                        stop=["</s>", "[INST]"],
                        echo=False
                    )
                    answer = response['choices'][0]['text'].strip()
                
                return answer
            raise e 