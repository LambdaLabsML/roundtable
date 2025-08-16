try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    print("OpenAI library not installed. Install with: pip install openai")
    OPENAI_AVAILABLE = False

from typing import List, Dict
from llm.base import LLMClient, retry_with_backoff
import asyncio
import logging

class LambdaClient(LLMClient):
    def __init__(self, api_key: str):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        if not api_key or api_key == "your_lambda_api_key_here":
            raise ValueError("Invalid Lambda API key. Please check your .env file")
        
        try:
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.lambda.ai/v1"
            )
            logging.info("Lambda client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Lambda client: {e}")
            raise
    
    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        async def _generate():
            try:
                messages_formatted = [{"role": "system", "content": system_prompt}] + messages
                
                # Convert to sync call wrapped in async
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model="deepseek-llama3.3-70b",
                    messages=messages_formatted,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if response and response.choices and response.choices[0].message:
                    return response.choices[0].message.content
                else:
                    raise ValueError("Empty response from Lambda API")
                    
            except openai.APIError as e:
                logging.error(f"Lambda API error: {e}")
                raise
            except Exception as e:
                logging.error(f"Unexpected error calling Lambda API: {e}")
                raise
        
        return await retry_with_backoff(_generate)