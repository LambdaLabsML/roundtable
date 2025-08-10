from abc import ABC, abstractmethod
from typing import List, Dict
import asyncio
import logging

class RetryableError(Exception):
    pass

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
    """Retry with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Max retries exceeded: {e}")
                raise
            delay = base_delay * (2 ** attempt)
            logging.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
            await asyncio.sleep(delay)
    return ""
