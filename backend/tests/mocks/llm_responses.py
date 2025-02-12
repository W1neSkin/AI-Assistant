class MockLLMResponse:
    DEFAULT_RESPONSE = "This is a mock response from the LLM"
    
    @staticmethod
    def get_mock_response(prompt: str) -> str:
        # Add different responses based on prompt content
        if "database" in prompt.lower():
            return "This query requires database access"
        elif "document" in prompt.lower():
            return "This query is about document content"
        return MockLLMResponse.DEFAULT_RESPONSE

class MockCloudLLM:
    async def generate_answer(self, prompt: str) -> str:
        return MockLLMResponse.get_mock_response(prompt)

    async def initialize(self):
        pass

class MockLocalLLM:
    async def generate_answer(self, prompt: str) -> str:
        return MockLLMResponse.get_mock_response(prompt)

    async def initialize(self):
        pass 