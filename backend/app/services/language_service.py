from urllib.parse import unquote
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

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
        # Extract different parts of context
        context_parts = []
        
        # Split context into sections if they exist
        sections = context.split('\n\n')
        for section in sections:
            if section.startswith('Document Context:'):
                context_parts.append(section)
            elif section.startswith('Database Results:'):
                # Format database results more clearly
                db_lines = section.split('\n')
                if len(db_lines) > 1:
                    results = db_lines[1:]  # Skip the "Database Results:" header
                    context_parts.append(
                        "Database Results:\n" + 
                        "- " + "\n- ".join(results)
                    )
            elif section.strip():
                context_parts.append(section)
        
        # Combine all context parts
        formatted_context = '\n\n'.join(context_parts)
        
        if self.is_russian(question):
            return (
                "<s>[INST] Ты русскоязычный ассистент телекоммуникационной компании. "
                "Твоя задача - отвечать ТОЛЬКО на русском языке. "
                "Используй ТОЛЬКО информацию из предоставленного контекста. "
                f"Вопрос: {question}\n\n"
                f"Контекст: {formatted_context} [/INST]</s>"
            )
        else:
            return (
                "<s>[INST] You are a helpful assistant from a telecommunication company. "
                "Please provide a detailed answer based on the given context. "
                f"Question: {question}\n\n"
                f"Context: {formatted_context} [/INST]</s>"
            ) 