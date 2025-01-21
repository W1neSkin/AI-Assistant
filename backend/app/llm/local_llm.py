from llama_cpp import Llama
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class LocalLLM:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
    
    async def initialize(self):
        """Initialize the local LLM model"""
        try:
            logger.info(f"Initializing local LLM with model: {self.model_path}")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,  # Context window
                n_threads=4,  # CPU threads
                verbose=False
            )
            logger.info("Local LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize local LLM: {str(e)}")
            raise

    async def generate_answer(self, prompt: str) -> str:
        """Generate answer using local LLM"""
        try:
            # 1. Initialize model if needed
            if not self.model:
                await self.initialize()

            # 2. Generate completion
            response = self.model.create_completion(
                prompt=prompt,
                max_tokens=512,
                top_k=40,
                top_p=0.95,
                repeat_penalty=1.1
            )
            
            # 3. Return cleaned response
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise

    def estimate_tokens(self, text: str) -> int:
        return int(len(text.encode('utf-8')) / 3)

    def truncate_context(self, context: str, max_tokens: int) -> str:
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