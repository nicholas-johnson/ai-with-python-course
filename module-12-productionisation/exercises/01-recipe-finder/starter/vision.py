"""Vision — identify ingredients from a photo using OpenAI vision."""

from openai import OpenAI
from .config import OPENAI_MODEL


client = OpenAI()


def identify_ingredients(image_base64: str) -> str:
    """Use OpenAI vision to identify ingredients visible in a food photo.

    Steps:
    1. Call client.chat.completions.create with OPENAI_MODEL
    2. System prompt: instruct the model to list ingredients as a comma-separated list
    3. User message: include the image as an image_url with base64 data URI
    4. Return the response text stripped of whitespace
    """
    # TODO: implement vision-based ingredient identification
    return "unknown ingredients"
