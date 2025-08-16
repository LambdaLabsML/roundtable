import os
from dotenv import load_dotenv

load_dotenv()

API_KEYS = {
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "google": os.getenv("GOOGLE_API_KEY"),
    "lambda": os.getenv("LAMBDA_API_KEY")
}

# Print diagnostic info
print("Loading API keys...")
for service, key in API_KEYS.items():
    if key and key != f"your_{service}_api_key_here":
        # Only show first and last 4 characters for security
        masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
        print(f"  {service}: {masked}")
    else:
        print(f"  {service}: NOT SET")
