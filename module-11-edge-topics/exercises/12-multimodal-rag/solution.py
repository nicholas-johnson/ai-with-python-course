"""
Exercise 12 — Multimodal RAG (Solution)

Index and search both text and images in a unified vector store
by describing images with a vision model before embedding.
"""

import math
import base64
from openai import OpenAI


def describe_image(client: OpenAI, image_path: str) -> str:
    """
    Use a vision model to generate a text description of an image.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Describe this image in detail for a search index. "
                        "Include all visible objects, text, colors, and layout."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}",
                    },
                },
            ],
        }],
    )
    return response.choices[0].message.content


def embed_text(client: OpenAI, text: str) -> list[float]:
    """
    Get an embedding vector for text.
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def index_item(client: OpenAI, item: dict) -> dict:
    """
    Create an index entry for a text or image item.
    """
    if item["type"] == "text":
        text = item["content"]
        source = ""
    elif item["type"] == "image":
        text = describe_image(client, item["path"])
        source = item["path"]
    else:
        raise ValueError(f"Unknown item type: {item['type']}")

    embedding = embed_text(client, text)

    return {
        "id": item["id"],
        "type": item["type"],
        "text": text,
        "embedding": embedding,
        "source": source,
    }


def build_multimodal_index(client: OpenAI, items: list[dict]) -> list[dict]:
    """
    Build a multimodal index from a list of text and image items.
    """
    return [index_item(client, item) for item in items]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_index(
    client: OpenAI,
    query: str,
    index: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Search the multimodal index with a text query.
    """
    query_emb = embed_text(client, query)
    scored = []
    for entry in index:
        sim = cosine_similarity(query_emb, entry["embedding"])
        scored.append({**entry, "score": sim})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
