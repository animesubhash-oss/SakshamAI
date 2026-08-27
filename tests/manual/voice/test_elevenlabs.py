import os
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs


# --------------------------------------------------
# Load .env from chatbot-voice
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)

print("Looking for .env at:")
print(ENV_FILE)

api_key = os.getenv("ELEVENLABS_API_KEY")

if not api_key:
    raise ValueError(
        "ELEVENLABS_API_KEY is not set. "
        f"Check your .env file at: {ENV_FILE}"
    )

print("ElevenLabs API key loaded successfully!")

client = ElevenLabs(api_key=api_key)

print("ElevenLabs client initialized successfully!")