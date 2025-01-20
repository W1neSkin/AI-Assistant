from typing import Dict, Any, Optional
from app.core.service_container import ServiceContainer
from app.services.sql_generator import SQLGenerator
import logging
import time
from urllib.parse import unquote

logger = logging.getLogger(__name__)

class QAService:
    def __init__(self):
        # Get services from container
        container = ServiceContainer.get_instance()
        self.llm_service = container.llm_service
        self.db_service = container.db_service
        self.url_service = container.url_service
        self.index_service = container.index_service
        self.lang_service = container.lang_service
        self.cache_service = container.cache_service
        self.sql_generator = container.sql_generator
        if not self.sql_generator:
            raise RuntimeError("Services not initialized. Call initialize() first")

    async def get_answer(
        self, 
        query: str, 
        model_type: str,
        enable_doc_search: bool = True
    ) -> Dict[str, Any]:
        """Process question and return answer with context"""
        try:
            start_time = time.time()
            # Double decode to handle URLs in the query
            decoded_query = unquote(unquote(query))
            
            # Switch model if requested
            if model_type:
                await self.llm_service.switch_provider(model_type)
            
            # Handle URLs in query
            url_data = await self.url_service.extract_and_process_urls(decoded_query)
            
            # Check if question requires database access
            db_data = None
            if await self.llm_service.is_db_question(decoded_query):
                db_data = await self._get_db_data(decoded_query)
            
            # Get relevant documents only if enabled
            doc_data = None
            if enable_doc_search:
                doc_data = await self.index_service.query_index(decoded_query)
            
            # Format context text with documents, URLs, and DB data
            context_text = await self._build_context(doc_data, url_data, db_data)
            
            # Format prompt based on language
            prompt = self.lang_service.format_prompt(decoded_query, context_text)
            
            # Generate answer using specified model
            answer = await self.llm_service.generate_answer(prompt)
            
            # Translate response if necessary
            if lang_info["language"] != "english":
                answer = await self.lang_service.translate_to_language(
                    answer, 
                    lang_info["language"]
                )
            
            return {
                "answer": answer,
                "context": doc_data,
                "db_data": db_data,
                "time_taken": round(time.time() - start_time, 2)
            }
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            raise

    async def _get_db_data(self, question: str) -> Optional[Dict[str, Any]]:
        """Get data from database if question requires it"""
        try:
            # Use SQLGenerator for query generation
            sql_query = await self.sql_generator.generate_query(question=question)
            results = await self.db_service.execute_query(sql_query)
            return {
                "sql_query": sql_query,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error getting DB data: {str(e)}")
            return None

    async def _build_context(
        self, 
        doc_data: Optional[Dict], 
        url_data: Optional[Dict],
        db_data: Optional[Dict]
    ) -> str:
        """Build context text from all available sources"""
        context_parts = []
        
        if doc_data:
            context_parts.append(' '.join([node['text'] for node in doc_data['source_nodes']]))
        
        if url_data:
            context_parts.append('\n'.join(url_data.get('contents', [])))
        
        if db_data:
            context_parts.append(f"Database Results: {db_data.get('results')}")
        
        return '\n\n'.join(context_parts)
