import os
from dotenv import load_dotenv

load_dotenv()

API_KEYS = {
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "google": os.getenv("GOOGLE_API_KEY")
}

# Validate API keys
for service, key in API_KEYS.items():
    if not key:
        print(f"Warning: Missing API key for {service}. Please set {service.upper()}_API_KEY in .env file")
