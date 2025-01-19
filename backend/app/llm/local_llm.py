from llama_cpp import Llama
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

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
    
    async def generate_answer(self, prompt: str) -> str:
        """Generate answer from a formatted prompt."""
        try:
            response = self.model.create_completion(
                prompt=prompt,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                stop=["</s>", "[INST]", "Human:", "Assistant:"],
                echo=False
            )
            
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