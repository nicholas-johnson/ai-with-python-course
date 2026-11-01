"""Part 2: The same image, parsed into a schema."""

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
DEMO_DIR = Path(__file__).parent


class ImageAnalysis(BaseModel):
    description: str = Field(description="A detailed description of the image")
    key_points: list[str] = Field(description="The most important observations")


def demo_vision_structured(client: OpenAI):
    print("=" * 60)
    print("PART 2: VISION — STRUCTURED")
    print("=" * 60)
    print()

    image_path = DEMO_DIR / "sample.webp"
    img_b64 = base64.b64encode(image_path.read_bytes()).decode()

    print(f"  Image: {image_path.name} ({image_path.stat().st_size} bytes)")
    print(f"  Sending to {MODEL} for analysis...\n")

    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=ImageAnalysis,
        input=[
            {"role": "system", "content": "You are an image analysis assistant."},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Describe and analyse this image in detail."},
                    {"type": "input_image", "image_url": f"data:image/webp;base64,{img_b64}"},
                ],
            },
        ],
    )

    result = response.output_parsed
    if result is None:
        print("  The model declined to analyse this image.")
        return
    print(f"  Description: {result.description}\n")
    print("  Key points:")
    for point in result.key_points:
        print(f"    • {point}")

    usage = response.usage
    print(f"\n  Tokens: {usage.input_tokens} prompt + {usage.output_tokens} completion")
    print("\n  The same API call powers the /vision endpoint in Exercise 2.")
