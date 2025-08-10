try:
    import google.generativeai as genai
except ImportError:
    print("Google Generative AI library not installed. Install with: pip install google-generativeai")
    genai = None

from typing import List, Dict
from llm.base import LLMClient, retry_with_backoff
import asyncio

class GeminiClient(LLMClient):
    def __init__(self, api_key: str):
        if not genai:
            raise ImportError("Google Generative AI library not installed")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        async def _generate():
            # Format messages for Gemini
            formatted_prompt = system_prompt + "\n\n"
            for msg in messages:
                formatted_prompt += f"{msg['role']}: {msg['content']}\n\n"
            
            # Convert to sync call wrapped in async
            response = await asyncio.to_thread(
                self.model.generate_content,
                formatted_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            return response.text
        
        return await retry_with_backoff(_generate)
