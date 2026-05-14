# Exercise 03 — HyDE (Hypothetical Document Embeddings)

## Recap

Query-document mismatch is a core problem in vector search: short questions land far from detailed documents in embedding space. **HyDE** bridges this gap by generating a hypothetical answer first, embedding that answer, and searching with the resulting vector. The hypothetical document is structurally closer to real documents than the original query.

## Your Task

1. Implement `generate_hypothetical_document(client, query)` — use the LLM to generate a plausible answer paragraph.
2. Implement `embed_text(client, text)` — get an embedding vector for text.
3. Implement `hyde_search(client, query, collection)` — the full HyDE pipeline.

## Steps

1. Open `start.py` and read the function signatures.
2. Implement `generate_hypothetical_document`: prompt the LLM to write a paragraph that would answer the query.
3. Implement `embed_text`: call the embeddings API.
4. Implement `hyde_search`: generate → embed → search.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/03-hyde/test_start.py -v
```

## Stretch Goals

- Average the original query embedding with the HyDE embedding.
- Generate multiple hypothetical documents and average their embeddings.
- Compare retrieval quality with and without HyDE on sample queries.
