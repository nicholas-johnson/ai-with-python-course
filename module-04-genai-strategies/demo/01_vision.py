"""Part 1: One image in, a text description out.
Run alone:  python module-04-genai-strategies/demo/01_vision.py
"""

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
DEMO_DIR = Path(__file__).parent


def demo_vision(client: OpenAI):
    print("=" * 60)
    print("PART 1: VISION")
    print("=" * 60)
    print()

    image_path = DEMO_DIR / "sample.webp"
    img_b64 = base64.b64encode(image_path.read_bytes()).decode()

    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Describe this image in one sentence."},
                    {"type": "input_image", "image_url": f"data:image/webp;base64,{img_b64}"},
                ],
            },
        ],
    )
    print(response.output_text)
    print()


if __name__ == "__main__":
    demo_vision(OpenAI())
