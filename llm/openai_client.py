try:
    import openai
except ImportError:
    print("OpenAI library not installed. Install with: pip install openai")
    openai = None

from typing import List, Dict
from llm.base import LLMClient, retry_with_backoff
import asyncio

class GPTClient(LLMClient):
    def __init__(self, api_key: str):
        if not openai:
            raise ImportError("OpenAI library not installed")
        self.client = openai.OpenAI(api_key=api_key)
    
    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        async def _generate():
            messages_formatted = [{"role": "system", "content": system_prompt}] + messages
            # Convert to sync call wrapped in async
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4-turbo-preview",  # Using GPT-4 as placeholder
                messages=messages_formatted,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        return await retry_with_backoff(_generate)
