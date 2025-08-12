try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    print("Anthropic library not installed. Install with: pip install anthropic")
    ANTHROPIC_AVAILABLE = False

from typing import List, Dict
from llm.base import LLMClient, retry_with_backoff
import asyncio
import logging

class ClaudeClient(LLMClient):
    def __init__(self, api_key: str):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")
        
        if not api_key or api_key == "your_anthropic_api_key_here" or not api_key.startswith("sk-ant-"):
            raise ValueError("Invalid Anthropic API key. Please check your .env file")
        
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            logging.info("Anthropic client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Anthropic client: {e}")
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
                # Validate inputs
                if not system_prompt or not system_prompt.strip():
                    raise ValueError("System prompt cannot be empty")
                
                if not messages:
                    raise ValueError("Messages list cannot be empty")
                
                # Validate message format
                for i, msg in enumerate(messages):
                    if not isinstance(msg, dict):
                        raise ValueError(f"Message {i} must be a dictionary")
                    if "role" not in msg:
                        raise ValueError(f"Message {i} missing 'role' field")
                    if "content" not in msg:
                        raise ValueError(f"Message {i} missing 'content' field")
                    if msg["role"] not in ["user", "assistant"]:
                        raise ValueError(f"Message {i} has invalid role: {msg['role']}")
                    if not msg["content"] or not msg["content"].strip():
                        raise ValueError(f"Message {i} has empty content")
                
                # Log the request parameters for debugging
                logging.info(f"Making Anthropic API request with:")
                logging.info(f"  Model: claude-opus-4-1-20250805")
                logging.info(f"  System prompt length: {len(system_prompt)}")
                logging.info(f"  Messages count: {len(messages)}")
                logging.info(f"  Temperature: {temperature}")
                logging.info(f"  Max tokens: {max_tokens}")
                
                # Log first few messages for debugging
                for i, msg in enumerate(messages[:3]):
                    logging.info(f"  Message {i}: role={msg['role']}, content_length={len(msg['content'])}")
                
                # Convert to sync call wrapped in async
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model="claude-opus-4-1-20250805",
                    system=system_prompt,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if response and response.content:
                    return response.content[0].text
                else:
                    raise ValueError("Empty response from Anthropic API")
                    
            except anthropic.APIError as e:
                logging.error(f"Anthropic API error: {e}")
                logging.error(f"Error type: {type(e)}")
                logging.error(f"Error details: {e.message if hasattr(e, 'message') else 'No message'}")
                logging.error(f"Error status: {e.status if hasattr(e, 'status') else 'No status'}")
                logging.error(f"Error response: {e.response if hasattr(e, 'response') else 'No response'}")
                raise
            except Exception as e:
                logging.error(f"Unexpected error calling Anthropic: {e}")
                logging.error(f"Error type: {type(e)}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                raise
        
        return await retry_with_backoff(_generate)
