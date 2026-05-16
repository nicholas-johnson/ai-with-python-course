import json
import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_preferences() -> dict:
    """Load user preferences from preferences.json."""
    path = os.path.join(DATA_DIR, "preferences.json")
    with open(path) as f:
        return json.load(f)
