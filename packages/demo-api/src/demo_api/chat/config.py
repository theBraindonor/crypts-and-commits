import os
from pathlib import Path

from dotenv import load_dotenv

DEMO_API_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(DEMO_API_ROOT / ".env")

DEFAULT_CHAT_MODEL = "google/gemma-4-31b-it"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_openrouter_api_key() -> str | None:
    return os.environ.get("OPENROUTER_API_KEY")


def get_chat_model_name() -> str:
    return os.environ.get("CHAT_MODEL", DEFAULT_CHAT_MODEL)
