try:
    import anthropic
except ImportError:
    print("Anthropic library not installed. Install with: pip install anthropic")
    anthropic = None

from typing import List, Dict
from llm.base import LLMClient, retry_with_backoff
import asyncio

class ClaudeClient(LLMClient):
    def __init__(self, api_key: str):
        if not anthropic:
            raise ImportError("Anthropic library not installed")
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def generate_response(
        self, 
        system_prompt: str, 
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        async def _generate():
            # Convert to sync call wrapped in async
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-opus-20240229",
                system=system_prompt,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text
        
        return await retry_with_backoff(_generate)
