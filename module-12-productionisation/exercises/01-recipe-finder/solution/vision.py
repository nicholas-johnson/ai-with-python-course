"""Vision — identify ingredients from a photo using OpenAI vision."""

from openai import OpenAI
from .config import OPENAI_MODEL


client = OpenAI()


def identify_ingredients(image_base64: str) -> str:
    """Use OpenAI vision to identify ingredients visible in a food photo."""
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a food ingredient identifier. "
                    "List the ingredients you can see in this image. "
                    "Return a short comma-separated list, nothing else."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    }
                ],
            },
        ],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()
