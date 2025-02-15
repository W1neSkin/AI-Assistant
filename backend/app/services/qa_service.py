import time
from typing import Dict, Any, Optional

from app.utils.logger import setup_logger
from app.db.sql_generator import SQLGenerator
from app.models.user import User
from app.utils.prompt_generator import PromptGenerator


logger = setup_logger(__name__)

class QAService:
    def __init__(self):
        self.llm_service = None
        self.index_service = None
        self.url_service = None
        self.cache_service = None

    def initialize(self, llm_service, index_service, url_service, cache_service):
        """Initialize with required services"""
        self.llm_service = llm_service
        self.index_service = index_service
        self.url_service = url_service
        self.cache_service = cache_service

    async def close(self):
        self.llm_service = None
        self.index_service = None
        self.url_service = None
        self.cache_service = None

    async def get_answer(self, query: str, user: User) -> dict:
        """Get answer for the query"""
        try:
            start_time = time.time()
            logger.info(f"Processing question: '{query}' with model: {self.llm_service.current_provider}")
            
            
            # Use model type from settings if set
            if user.use_cloud:
                model_type = "cloud"
                logger.info(f"Settings indicate cloud model should be used (current: {self.llm_service.current_provider})")
            else:
                model_type = "local"
                logger.info(f"Settings indicate local model should be used (current: {self.llm_service.current_provider})")
            
            # Switch to the correct model if specified
            if model_type and model_type != self.llm_service.current_provider:
                logger.info(f"Model switch needed: {self.llm_service.current_provider} -> {model_type}")
                await self.llm_service.change_provider(model_type)
                logger.info(f"Switched to {model_type} model")
            else:
                logger.info(f"Using current model: {self.llm_service.current_provider}")
            
            # 1. Handle URLs in question
            url_contents = []
            if user.handle_urls and self.url_service:
                urls = await self.url_service.extract_urls(query)
                if urls:
                    logger.info(f"Found URLs in question: {urls}")
                for url in urls:
                    content = await self.url_service.fetch_url_content(url)
                    if content:
                        logger.info(f"Successfully fetched content from {url}")
                        url_contents.append(content)
                    else:
                        logger.warning(f"Failed to fetch content from {url}")
            
            # 2. Check if question needs DB access
            db_data = None
            if user.check_db and self.llm_service:
                needs_db = await self.llm_service.is_db_question(query)
                logger.info(f"Question requires DB access: {needs_db}")
                if needs_db:
                    db_data = await self._get_db_data(query)
                    if db_data:
                        logger.info(f"Retrieved DB data with query: {db_data.get('sql_query')}")
            
            # 3. Get document context if enabled
            context = ""
            source_nodes = []
            if user.enable_document_search:
                logger.info("Searching document context...")
                try:
                    doc_data = await self._get_document_data(query, str(user.id))
                    if doc_data:
                        source_nodes = doc_data['source_nodes']
                except Exception as e:
                    logger.error(f"Error searching documents: {str(e)}")
            
            # 4. Combine all context sources
            context = await self._build_context(doc_data, url_contents, db_data)
                        
            # 5. Format prompt with all context
            logger.info("Preparing prompt according question language...")
            prompt = PromptGenerator.format_prompt(
                question=query,
                context=context
            )
            
            logger.info(f"Generated prompt (length: {len(prompt)} chars)")
            logger.debug(f"Full prompt: {prompt}")
            
            # Get answer using appropriate model
            if user.use_cloud:
                answer = await self.llm_service.generate_answer(prompt)
            else:
                answer = await self.llm_service.generate_answer(prompt)
            
            # Extract just the answer text, not the whole response dict
            answer_text = answer.get('answer') if isinstance(answer, dict) else answer
            logger.info(f"Generated answer (length: {len(answer_text)} chars)")
            logger.debug(f"Full answer: {answer_text}")
            
            time_taken = round(time.time() - start_time, 2)
            logger.info(f"Request completed in {time_taken}s")
            
            # Return properly structured response
            response = {
                "answer": str(answer_text),
                "context": {
                    "source_nodes": [
                        {
                            "filename": str(node['filename']),
                            "text": str(node['text'])
                        }
                        # Use a set to track seen filenames and only include first occurrence
                        for i, node in enumerate(source_nodes or [])
                        if node['filename'] not in {n['filename'] for n in (source_nodes or [])[:i]}
                    ],
                    "time_taken": float(time_taken)
                }
            }
            
            logger.debug(f"Returning response: {response}")
            return response
        except Exception as e:
            logger.exception(f"Error processing query '{query}': {str(e)}")
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
            from app.core.service_container import ServiceContainer  # Move import inside method
            container = ServiceContainer.get_instance()
            
            # Use SQLGenerator for query generation
            schema = await container.db_service.get_schema()
            sql_generator = SQLGenerator(
                schema=schema,
                llm_service=container.llm_service
            )
            
            sql_query = await sql_generator.generate_query(question=question)
            logger.info(f"Generated SQL query: {sql_query}")
            db_service = container.db_service
            results = await db_service.execute_query(sql_query)
            logger.info(f"Results from DB: {results}")
            return {
                "sql_query": sql_query,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error getting DB data: {str(e)}")
            return None

    async def _get_document_data(self, question: str, user_id: str) -> Optional[Dict]:
        """Get relevant document data if available"""
        try:
            results = await self.index_service.query(question, user_id)
            if results and len(results) > 0:
                return {
                    "source_nodes": results  # Results already have the right structure
                }
            return None
        except Exception as e:
            logger.error(f"Error getting document data: {str(e)}")
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
                context_parts.append("\n\nURL Context:\n" + "\n".join(url_data.get('contents', [])))
        if db_data:
                context_parts.append(f"\n\nDatabase Results:\n{db_data.get('results')}")
                if db_data.get('sql_query'):
                    context_parts.append(f"\nSQL Query Used: {db_data['sql_query']}")
        
        return '\n\n'.join(context_parts)
