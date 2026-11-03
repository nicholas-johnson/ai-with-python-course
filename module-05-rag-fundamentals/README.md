# Module 5 — RAG Fundamentals

> The Pathfinder's knowledge base is vast — ship logs spanning years, technical manuals, mission reports, and star system surveys. The LLM's context window cannot hold it all, and its training data is already stale. Retrieval-Augmented Generation (RAG) bridges the gap: chunk the documents, embed them, store them in a vector database, and at query time retrieve only the relevant passages before asking the model. The result is answers that are grounded in real data, with citations the crew can verify.

## Learning goals

- Split documents into **chunks** (fixed-size, sentence-aware, structure-aware, overlap) and **synthetic** units (extracted facts, generated FAQs).
- Generate **embeddings** with `text-embedding-3-small` and store in **ChromaDB**.
- Expand queries at search time with **query expansion** and **HyDE**.
- Build **grounded prompts** with source citations.
- Wrap a RAG pipeline as **MCP tools** any agent can call.

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
        if end >= len(text):
            break  # last chunk reached the end; another would sit inside its overlap
        start = end - overlap
    return chunks
```

**Overlap** ensures that a concept split across a boundary appears complete in at least one chunk. 50-100 characters of overlap is typical.

**Sentence-aware chunking** — split on sentence boundaries, then group sentences until the chunk reaches the size limit. Preserves natural language boundaries, avoids orphaned sentence fragments.

**Structure-aware chunking** — split on document structure (headers, paragraphs, code blocks). Ideal for Markdown, HTML, or log files with clear delimiters.

**Synthetic chunking** does not embed the raw slice. An LLM rewrites each passage into text a question will actually match, and you keep the original passage as what you retrieve and cite.

**Fact extraction** — one atomic claim per chunk. "Reactor efficiency fell to 72% after the ion storm." The claim embeds as a precise vector. Retrieve the source passage, so the model answers from the original and can cite it.

**FAQ extraction** — the questions that passage would answer. "What did the ion storm do to the reactor?" Embed the question. A crew question lands near a question, and the passage comes back with it.

Both cost a model call per passage at ingest time. They earn it when queries do not resemble the source wording. The synthetic text is the index, not the evidence.

| Strategy | Pros | Cons |
| -------- | ---- | ---- |
| Fixed-size | Simple, predictable | Cuts mid-sentence |
| Sentence-aware | Natural boundaries | Varying chunk sizes |
| Structure-aware | Preserves semantics | Needs format-specific parser |
| Fact extraction | Precise claim-level match | LLM cost; a claim can lose its surrounding context |
| FAQ extraction | Questions match questions | LLM cost; generated questions can drift from the source |

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
        dimensions=256,   # optional: shorter vectors from the same model
    )
    return [item.embedding for item in response.data]
```

`text-embedding-3-small` returns 1536 dimensions by default. Passing `dimensions` truncates the vector — 256 gives you a sixth of the storage and faster search, for a small drop in recall. Pick one and stay with it: changing the dimension means re-embedding and re-indexing the whole corpus, because vectors of different lengths cannot be compared.

For offline or local embedding, `sentence-transformers` provides open-source models that run without an API key. The trade-off is slightly lower quality on English benchmarks but zero cost per embedding.

Key considerations:
- Embed chunks and queries with the **same model** — mixing models produces misaligned vector spaces.
- Embedding dimension affects storage and speed — 256 is fast, 1536 is more expressive.
- Batch embedding calls to minimize round trips.

---

## Advanced techniques

These are the four things you add once the basic pipeline runs. Each is covered in depth in [Module 13](../module-13-edge-topics/); here is what they are and why you would reach for them.

**Hybrid search** — vector search matches meaning, keyword search (BM25) matches tokens. Ask for error code `FTL-4092` and the embedding has nothing to be similar to, because the code carries no semantics. Run both searches and merge the ranked lists with **Reciprocal Rank Fusion**: each document scores `1/(k + rank)` summed across lists, with `k` around 60. Because RRF uses rank positions, you never have to normalise BM25 scores against cosine distances.

**Re-ranking** — retrieval is tuned for recall, so it casts a wide net and orders it roughly. A cross-encoder reads the query and the passage together and scores the pair, catching negation and qualification that a bi-encoder averages away. The usual shape is: retrieve 50 cheaply, re-rank the top 25, send the top 5 to the model. You pay latency per candidate, so keep the candidate set small.

**Metadata filtering** — the metadata you store for citation is also a filter. ChromaDB takes a `where` clause that narrows the candidate set before ranking:

```python
collection.query(
    query_texts=["hull damage"],
    n_results=5,
    where={"department": "engineering"},        # exact match
)

collection.query(
    query_texts=["hull damage"],
    n_results=5,
    where={"stardate": {"$gte": 2287.0}},       # range
)
```

You can only filter on fields you stored at ingest time, which is another reason to be generous with metadata when you chunk.

**Semantic caching** — the crew asks the same question twenty different ways. Cache on the query *embedding* rather than the string, so "reactor status" hits the entry stored for "how is the reactor doing". Above a similarity threshold, return the cached answer and skip the pipeline. Set the threshold too low and you will confidently serve the answer to a different question. Re-indexing the corpus should drop the cache, or stale answers will outlive their sources.

---

## Synthetic query expansion

Synthetic chunking rewrites the corpus at ingest time. Query expansion rewrites the question at search time, for the same reason: a short question often sits far from the passage that answers it.

**Query expansion** — ask the model for a few alternate phrasings, embed each, search, and merge the hits. "What did the ion storm do to the reactor?" also searches "reactor output after the storm" and "efficiency drop, ion storm". The question stays a question. Answer from the passages you retrieved, not from the rewrites.

**HyDE** (Hypothetical Document Embeddings) — ask the model to write a passage that would answer the question, even if it has to guess. Embed that passage instead of the question. A made-up log entry lives in the same region of vector space as real log entries, so nearest-neighbour search finds them. Discard the hypothetical text. It is a search vector, not a source.

Both cost a model call on every query. They earn it when the crew's wording does not resemble the logs.

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

Beyond those two, **pgvector** is a Postgres extension that keeps vectors beside your relational data, so one query can join an embedding search to the rest of your schema. **Qdrant** and **Weaviate** are dedicated servers with metadata filtering and hybrid search built in. **Pinecone** is fully hosted — you pay to have no infrastructure to run. They all do the same job; pick on where your data already lives and how much operational work you want.

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

## Summary

- **Chunk for retrieval, not for reading.** Smaller chunks with overlap beat whole-page dumps. Carry source metadata so a citation is possible.
- **Same model for docs and queries.** Embed both sides, store the vectors, and search. Mismatched models score garbage.
- **Ground every answer.** An answer without a source is just a hallucination with confidence.
- **The pipeline can be tools.** Wrap ingest and search as MCP tools any agent can call.

---

## Demos

The demo is a multi-step walkthrough using a persistent ChromaDB (via Docker). See [`demo/README.md`](demo/README.md) for full instructions.

```bash
# Option A: venv active. Option B: prefix python/mcp commands with 'uv run' (see demo/README.md).
cd module-05-rag-fundamentals/demo
docker compose up -d              # start ChromaDB
python ingest.py                  # load + chunk + embed + store
mcp dev server.py       # (optional) inspect tools in browser
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
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-05-rag-fundamentals/

# Option B - uv (no activation needed):
uv run --extra dev pytest module-05-rag-fundamentals/
```

## Slides

From repo root: `pnpm slides:05`, or `cd module-05-rag-fundamentals/slides && pnpm dev`.

## Reference

- [OpenAI — Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [ChromaDB docs](https://docs.trychroma.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [sentence-transformers](https://www.sbert.net/)
- [BM25 explained](https://en.wikipedia.org/wiki/Okapi_BM25)
- [HyDE — Precise Zero-Shot Dense Retrieval without Relevance Labels](https://arxiv.org/abs/2212.10496)
