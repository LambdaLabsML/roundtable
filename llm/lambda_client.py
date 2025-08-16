try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("Requests library not installed. Install with: pip install requests")
    REQUESTS_AVAILABLE = False

from typing import List, Dict
from llm.base import LLMClient, retry_with_backoff
import asyncio
import logging
import json

class LambdaClient(LLMClient):
    def __init__(self, api_key: str):
        if not REQUESTS_AVAILABLE:
            raise ImportError("Requests library not installed. Run: pip install requests")

        if not api_key or api_key == "your_lambda_api_key_here":
            raise ValueError("Invalid Lambda API key. Please check your .env file")

        self.api_key = api_key
        self.base_url = "https://api.lambda.ai/v1"
        self.model = "deepseek-llama3.3-70b"

        logging.info("Lambda client initialized successfully")

    async def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        async def _generate():
            try:
                # Format messages for Lambda API (OpenAI-compatible format)
                messages_formatted = [{"role": "system", "content": system_prompt}] + messages

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": self.model,
                    "messages": messages_formatted,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                # Make async HTTP request
                response = await asyncio.to_thread(
                    requests.post,
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                if response.status_code != 200:
                    error_msg = f"Lambda API error: {response.status_code} - {response.text}"
                    logging.error(error_msg)
                    raise Exception(error_msg)

                response_data = response.json()

                if (response_data and
                    "choices" in response_data and
                    response_data["choices"] and
                    "message" in response_data["choices"][0] and
                    "content" in response_data["choices"][0]["message"]):

                    return response_data["choices"][0]["message"]["content"]
                else:
                    raise ValueError("Empty or invalid response from Lambda API")

            except requests.exceptions.RequestException as e:
                logging.error(f"Lambda API request error: {e}")
                raise
            except json.JSONDecodeError as e:
                logging.error(f"Lambda API JSON decode error: {e}")
                raise
            except Exception as e:
                logging.error(f"Unexpected error calling Lambda API: {e}")
                raise

        return await retry_with_backoff(_generate)
