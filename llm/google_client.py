try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    print("Google Generative AI library not installed. Install with: pip install google-generativeai")
    GOOGLE_AVAILABLE = False

from typing import List, Dict
from llm.base import LLMClient, retry_with_backoff
import asyncio
import logging

class GeminiClient(LLMClient):
    def __init__(self, api_key: str):
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Generative AI library not installed. Run: pip install google-generativeai")
        
        if not api_key or api_key == "your_google_api_key_here" or not api_key.startswith("AIza"):
            raise ValueError("Invalid Google API key. Please check your .env file")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')
            logging.info("Google Gemini client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Google client: {e}")
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
                
                if response and response.text:
                    return response.text
                else:
                    raise ValueError("Empty response from Google API")
                    
            except Exception as e:
                logging.error(f"Error calling Google Gemini: {e}")
                raise
        
        return await retry_with_backoff(_generate)
