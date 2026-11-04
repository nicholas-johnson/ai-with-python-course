"""Vision — identify ingredients from a photo using OpenAI vision."""

from openai import OpenAI
from .config import OPENAI_MODEL


client = OpenAI()


def identify_ingredients(image_base64: str) -> str:
    """Use OpenAI vision to identify ingredients visible in a food photo."""
    response = client.responses.create(
        model=OPENAI_MODEL,
        reasoning={"effort": "none"},
        input=[
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
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64}",
                    }
                ],
            },
        ],
        max_output_tokens=150,
    )
    return response.output_text.strip()
