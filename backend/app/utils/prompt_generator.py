from urllib.parse import unquote
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class PromptGenerator:
    def is_russian(self, text: str) -> bool:
        """Check if text contains Russian characters."""
        try:
            decoded_text = unquote(text)
            return any(ord(char) >= 1040 and ord(char) <= 1103 for char in decoded_text)
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return False

    @staticmethod
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
    
    @staticmethod
    def format_prompt_for_sql(self, question: str, schema: str) -> str:
        prompt = f"""
        Given the following database schema:
        {schema}

        And this question:
        {question}

        Write a SQL query that answers this question.
        Rules:
        1. IMPORTANT: Return ONLY the SQL query - no explanations, no thinking steps, no markdown
        2. ONLY use SELECT statements - no ALTER, DROP, DELETE, UPDATE, INSERT, or other modifying statements
        3. Be safe and properly formatted
        4. Use explicit column names (no SELECT *)
        5. Include necessary JOINs and WHERE clauses
        6. Return only the data needed to answer the question
        7. Use proper SQL injection prevention practices
        8. Keep the query simple and efficient

        Format your response as a raw SQL query without any additional text or formatting.
        BAD: "Here's the query: SELECT..."
        BAD: ```sql SELECT...```
        GOOD: SELECT...
        """
        return prompt
    
    @staticmethod
    def format_prompt_for_is_question(self, question: str) -> str:
        prompt = f"""Analyze if this question requires database access.
        Return ONLY 'true' or 'false' without explanation.
        
        Guidelines:
        - Database is needed for questions about specific records, statistics, or data analysis
        - Database is NOT needed for general questions or document-based queries
        - Consider keywords like: show, find, count, list, how many, average, total
        
        Examples:
        - "Show me all clients from New York" -> true (requires database)
        - "What is machine learning?" -> false (general knowledge)
        - "How many orders were placed last month?" -> true (requires database)
        - "Explain the company's privacy policy" -> false (document-based)
        
        Question: {question}
        
        Think step by step:
        1. Identify key action words
        2. Check if question asks for specific data
        3. Determine if answer requires stored records
        """
        return prompt
