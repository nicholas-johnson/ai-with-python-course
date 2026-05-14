# Exercise 12 — Multimodal RAG

## Recap

Real-world knowledge bases contain images alongside text. **Multimodal RAG** extends retrieval to handle images by using a vision model to generate text descriptions, embedding those descriptions, and searching across modalities in a single vector store.

## Your Task

1. Implement `describe_image(client, image_path)` — use a vision model to describe an image.
2. Implement `index_item(client, item)` — create an embedding entry for a text chunk or image.
3. Implement `build_multimodal_index(client, items)` — index a mixed collection of text and images.
4. Implement `search_index(client, query, index)` — search the multimodal index.

## Steps

1. Open `start.py` and review the item format and function signatures.
2. Implement `describe_image`: send the image to gpt-4o-mini with a description prompt.
3. Implement `index_item`: for text items embed the text, for images describe then embed.
4. Build the full index in `build_multimodal_index`.
5. Implement `search_index` with cosine similarity.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/12-multimodal-rag/test_start.py -v
```

## Stretch Goals

- Pass actual images to the generation step for richer answers.
- Add metadata filtering (search only images, or only text).
- Implement cross-modal queries (text query → image results).
