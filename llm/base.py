from abc import ABC, abstractmethod
from typing import List, Dict
import asyncio
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)

class LLMClient(ABC):
    @abstractmethod
    async def generate_response(
        self, 
        system_prompt: str, 
        messages: List[Dict], 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        pass

async def retry_with_backoff(
    func, 
    max_retries: int = 3,
    base_delay: float = 1.0
) -> str:
    """Retry with exponential backoff and better error reporting"""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            result = await func()
            if result:  # Only return if we got a valid result
                return result
            else:
                raise ValueError("Empty response from API")
        except Exception as e:
            last_error = e
            error_details = traceback.format_exc()
            
            if attempt == max_retries - 1:
                logging.error(f"Max retries exceeded. Last error: {e}")
                logging.error(f"Full traceback: {error_details}")
                raise e
            
            delay = base_delay * (2 ** attempt)
            logging.warning(f"Attempt {attempt + 1} failed: {e}")
            logging.warning(f"Retrying in {delay}s...")
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_error:
        raise last_error
    return ""
