from typing import Dict, Any, Optional
import logging
from app.utils.logger import setup_logger
import time
from urllib.parse import unquote
from app.services.sql_generator import SQLGenerator


logger = setup_logger(__name__)

class QAService:
    def __init__(self):
        self.llm_service = None
        self.index_service = None
        self.url_service = None
        self.cache_service = None
        self.lang_service = None

    def initialize(self, llm_service, index_service, url_service, cache_service, lang_service):
        """Initialize with required services"""
        self.llm_service = llm_service
        self.index_service = index_service
        self.url_service = url_service
        self.cache_service = cache_service
        self.lang_service = lang_service

    async def get_answer(
        self, 
        question: str, 
        model_type: str = None,
        include_docs: bool = True
    ) -> Dict[str, Any]:
        """Get answer for the question"""    
        try:
            start_time = time.time()
            logger.info(f"Processing question: '{question}' with model: {model_type}")
            
            # 1. Handle URLs in question
            url_contents = []
            # if self.url_service:
            #     urls = await self.url_service.extract_urls(question)
            #     if urls:
            #         logger.info(f"Found URLs in question: {urls}")
            #     for url in urls:
            #         content = await self.url_service.fetch_url_content(url)
            #         if content:
            #             logger.info(f"Successfully fetched content from {url}")
            #             url_contents.append(content)
            #         else:
            #             logger.warning(f"Failed to fetch content from {url}")
            
            # 2. Check if question needs DB access
            db_data = None
            # if self.llm_service:
            #     needs_db = await self.llm_service.is_db_question(question)
            #     logger.info(f"Question requires DB access: {needs_db}")
            #     if needs_db:
            #         db_data = await self._get_db_data(question)
            #         if db_data:
            #             logger.info(f"Retrieved DB data with query: {db_data.get('sql_query')}")
            
            # 3. Get document context if enabled
            context = ""
            source_nodes = []
            # if include_docs:
            #     logger.info("Searching document context...")
            #     query_bundle, search_results = await self.index_service.query(question)
            #     source_nodes = search_results
            #     logger.info(f"Found {len(source_nodes)} relevant document nodes")
            #     if source_nodes:
            #         context += "\n\nDocument Context:\n"
            #         for node in source_nodes:
            #             if node['text'].strip():  # Only add non-empty text
            #                 context += f"\nFrom {node['filename']}:\n{node['text']}\n"
            #                 context += f"(Relevance Score: {node['similarity_score']:.2f})\n"
            #     else:
            #         context += "\n\nNo relevant documents found."
            
            # 4. Combine all context sources
            if url_contents:
                context += "\n\nURL Context:\n" + "\n".join(url_contents)
            if db_data:
                context += f"\n\nDatabase Results:\n{db_data['results']}"
                if db_data.get('sql_query'):
                    context += f"\nSQL Query Used: {db_data['sql_query']}"
            
            # 5. Format prompt with all context
            logger.info("Preparing prompt according question language...")
            # prompt = self.lang_service.format_prompt(
            #     question=question,
            #     context=context
            # )
            prompt = question
            
            logger.info(f"Generated prompt (length: {len(prompt)} chars)")
            logger.debug(f"Full prompt: {prompt}")
            
            answer = await self.llm_service.generate_answer(prompt)
            # Extract just the answer text, not the whole response dict
            answer_text = answer.get('answer') if isinstance(answer, dict) else answer
            logger.info(f"Generated answer (length: {len(answer_text)} chars)")
            logger.debug(f"Full answer: {answer_text}")
            
            time_taken = round(time.time() - start_time, 2)
            logger.info(f"Request completed in {time_taken}s")
            
            # Return properly structured response
            response = {
                "answer": str(answer_text),  # Use the extracted answer text
                "context": {
                    "source_nodes": [
                        {
                            "filename": str(node['filename']),
                            "text": str(node['text'])
                        }
                        for node in (source_nodes or [])
                    ],
                    "time_taken": float(time_taken)
                }
            }
            
            logger.debug(f"Returning response: {response}")
            return response
        except Exception as e:
            logger.exception(f"Error processing query '{question}': {str(e)}")
            # Return a properly structured error response
            return {
                "answer": f"Error: {str(e)}",
                "context": {
                    "source_nodes": [],
                    "time_taken": 0
                }
            }

    async def _get_db_data(self, question: str) -> Optional[Dict[str, Any]]:
        """Get data from database if question requires it"""
        try:
            from app.core.service_container import ServiceContainer
            container = ServiceContainer.get_instance()
            
            # Use SQLGenerator for query generation
            schema = await container.db_service.get_schema()
            sql_generator = SQLGenerator(
                schema=schema,
                llm_service=container.llm_service
            )
            await sql_generator.initialize()
            
            sql_query = await sql_generator.generate_query(question=question)
            logger.info(f"Generated SQL query: {sql_query}")
            db_service = container.db_service
            results = await db_service.execute_query(sql_query)
            logger.info(f"Results: {results}")
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
