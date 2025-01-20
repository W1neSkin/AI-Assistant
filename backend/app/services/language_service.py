from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

class LanguageService:
    def is_russian(self, text: str) -> bool:
        """Check if text contains Russian characters."""
        try:
            decoded_text = unquote(text)
            return any(ord(char) >= 1040 and ord(char) <= 1103 for char in decoded_text)
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return False

    def format_prompt(self, question: str, context: str) -> str:
        """Format prompt based on language."""
        if self.is_russian(question):
            return (
                "<s>[INST] Ты русскоязычный ассистент. "
                "Твоя задача - отвечать ТОЛЬКО на русском языке. "
                "Используй ТОЛЬКО информацию из предоставленного контекста. "
                f"Вопрос: {question}\n\n"
                f"Контекст: {context} [/INST]</s>"
            )
        else:
            return (
                "<s>[INST] You are a helpful assistant. "
                "Please provide a detailed answer based on the given context. "
                f"Question: {question}\n\n"
                f"Context: {context} [/INST]</s>"
            ) 