# Module 5 — RAG Fundamentals

> The Pathfinder's knowledge base is vast — ship logs spanning years, technical manuals, mission reports, and star system surveys. The LLM's context window cannot hold it all, and its training data is already stale. Retrieval-Augmented Generation (RAG) bridges the gap: chunk the documents, embed them, store them in a vector database, and at query time retrieve only the relevant passages before asking the model. The result is answers that are grounded in real data, with citations the crew can verify.

## Learning goals

- Split documents into **chunks** (fixed-size, sentence-aware, structure-aware, overlap).
- Generate **embeddings** with `text-embedding-3-small` or `sentence-transformers`.
- Store and query vectors in **chromadb** and understand how FAISS works.
- Compare **dense**, **sparse**, and **hybrid** retrieval strategies.
- Build **grounded prompts** with source citations.
- Evaluate RAG with **recall**, **precision**, and **faithfulness** metrics.

---

## The RAG pipeline

RAG adds a retrieval step before generation. Instead of asking the LLM a question cold, you first search your document store for relevant passages, then include those passages in the prompt so the model can answer from evidence.

```
User query
    ↓
[Embed query] → [Search vector store] → top-k passages
    ↓
[Build grounded prompt with passages]
    ↓
[LLM generates answer with citations]
```

Every RAG system has four stages: **chunk** (split documents), **embed** (convert to vectors), **store** (index for search), and **retrieve** (find relevant chunks at query time). Get any of these wrong and the whole pipeline suffers.

---

## Chunking strategies

A ship log entry might be 50 words or 5,000 words. You cannot embed an entire 50-page manual as one vector — the embedding would average out the meaning and match nothing well. You need to split documents into chunks that are small enough to be specific but large enough to be coherent.

**Fixed-size chunking** — split every N characters (or tokens). Simple and predictable, but cuts mid-sentence.

```python
def chunk_fixed(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

**Overlap** ensures that a concept split across a boundary appears complete in at least one chunk. 50-100 characters of overlap is typical.

**Sentence-aware chunking** — split on sentence boundaries, then group sentences until the chunk reaches the size limit. Preserves natural language boundaries, avoids orphaned sentence fragments.

**Structure-aware chunking** — split on document structure (headers, paragraphs, code blocks). Ideal for Markdown, HTML, or log files with clear delimiters.

| Strategy | Pros | Cons |
| -------- | ---- | ---- |
| Fixed-size | Simple, predictable | Cuts mid-sentence |
| Sentence-aware | Natural boundaries | Varying chunk sizes |
| Structure-aware | Preserves semantics | Needs format-specific parser |

Every chunk should carry **metadata** for citation: source file, chunk index, page/line number. Without metadata, the model cannot tell the user where it got its answer.

---

## Embeddings

An embedding converts text into a dense numeric vector (typically 256-1536 dimensions). Texts with similar meaning produce vectors that are close together in this space. At query time, you embed the question and find the stored vectors nearest to it.

```python
from openai import OpenAI
client = OpenAI()

def embed(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]
```

For offline or local embedding, `sentence-transformers` provides open-source models that run without an API key. The trade-off is slightly lower quality on English benchmarks but zero cost per embedding.

Key considerations:
- Embed chunks and queries with the **same model** — mixing models produces misaligned vector spaces.
- Embedding dimension affects storage and speed — 256 is fast, 1536 is more expressive.
- Batch embedding calls to minimize round trips.

---

## Vector stores

Once you have embeddings, you need a place to store and search them. A vector store indexes vectors for approximate nearest-neighbour (ANN) search.

**chromadb** is the simplest option — an in-process vector database that stores embeddings, metadata, and original text together.

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("ship_logs")
collection.add(
    documents=chunks,
    metadatas=[{"source": f"log_{i}"} for i in range(len(chunks))],
    ids=[f"chunk_{i}" for i in range(len(chunks))],
)

results = collection.query(
    query_texts=["hull damage sector 7"],
    n_results=5,
)
```

**FAISS** (Facebook AI Similarity Search) is lower-level — you manage the index directly. It is faster for large collections (millions of vectors) but requires more code. ChromaDB is preferred for course exercises; FAISS is what you use in production at scale.

---

## Retrieval strategies

**Dense retrieval** embeds the query and finds nearest neighbours. Great for semantic similarity ("damage to the ship" matches "hull breach detected") but can miss exact terms.

**Sparse retrieval** (BM25 / TF-IDF) matches on exact keywords. Good for specific identifiers ("CRW-003", "MSN-001") that dense embeddings treat as opaque tokens.

**Hybrid search** combines both: run dense and sparse in parallel, merge the ranked results. This is the production standard — you get semantic understanding and keyword precision.

**Reranking** takes the top results from retrieval and rescores them with a more expensive model (cross-encoder). It improves precision at the cost of latency. Run retrieval to get 20 candidates, rerank to pick the best 5.

| Strategy | Strength | Weakness |
| -------- | -------- | -------- |
| Dense | Semantic matching | Misses exact terms |
| Sparse (BM25) | Exact keyword matching | Misses synonyms |
| Hybrid | Best of both | Two indices to maintain |
| Reranking | High precision | Adds latency |

---

## Grounded prompts with citations

The whole point of RAG is grounding: the model's answer should be based on retrieved evidence, not its training data. Build the prompt to make this explicit:

```python
def build_grounded_prompt(query: str, passages: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source {i+1}: {p['source']}]\n{p['text']}"
        for i, p in enumerate(passages)
    )
    return f"""Answer the question using ONLY the sources below.
Cite sources as [Source N]. If the sources don't contain the answer, say so.

Sources:
{context}

Question: {query}
Answer:"""
```

The `[Source N]` format lets you trace every claim back to a chunk. Post-processing can link these references to original documents, pages, or timestamps for the crew to verify.

---

## RAG evaluation

A RAG pipeline is only as good as its retrieval. Evaluate with:

- **Recall@k** — of all relevant chunks, how many appear in the top k results?
- **Precision@k** — of the top k results, how many are actually relevant?
- **Faithfulness** — does the generated answer only contain information from the retrieved passages? (Test by checking for claims not in any source.)

Build a set of test queries with known relevant chunks, then measure these metrics automatically. Run the eval suite after every change to the chunking strategy, embedding model, or retrieval parameters.

---

## Field rules

- **Chunk for retrieval, not for reading.** 300-500 tokens per chunk is the sweet spot.
- **Always carry metadata.** Source, index, and timestamp make citations possible.
- **Hybrid beats pure dense or pure sparse.** Use both for production RAG.
- **Evaluate continuously.** Recall and faithfulness metrics catch drift early.

---

## Demos

The demo is a multi-step walkthrough using a persistent ChromaDB (via Docker). See [`demo/README.md`](demo/README.md) for full instructions.

```bash
cd module-05-rag-fundamentals/demo
docker compose up -d              # start ChromaDB
python ingest.py                  # load + chunk + embed + store
python -m mcp dev server.py       # (optional) inspect tools in browser
python agent.py                   # chat with the RAG agent
docker compose down               # clean up
```

## Exercises

The three exercises chain together into a complete RAG system. Each builds on the last; you can bring your own code forward or use the provided solution from the previous exercise.

| Folder | What you build |
| ------ | -------------- |
| [`exercises/01-build-index`](exercises/01-build-index/) | Chunk ship logs, embed with OpenAI, store in ChromaDB, and search interactively. |
| [`exercises/02-rag-chat`](exercises/02-rag-chat/) | Build a grounded chat agent with source citations and `/norag` comparison. |
| [`exercises/03-rag-mcp-server`](exercises/03-rag-mcp-server/) | Wrap the RAG pipeline as an MCP server and connect it to a tool-calling agent. |

Run tests for this module:

```bash
pytest module-05-rag-fundamentals/
```

## Slides

From repo root: `pnpm slides:05`, or `cd module-05-rag-fundamentals/slides && pnpm dev`.

## Reference

- [OpenAI — Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [ChromaDB docs](https://docs.trychroma.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [sentence-transformers](https://www.sbert.net/)
- [BM25 explained](https://en.wikipedia.org/wiki/Okapi_BM25)
