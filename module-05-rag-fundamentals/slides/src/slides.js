export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 5 — RAG Fundamentals',
      subtitle: 'Retrieval-augmented generation from ingestion to citation',
      icon: 'book-open',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Why RAG?',
      points: [
        'LLMs hallucinate. Source documents do not.',
        'Retrieval-Augmented Generation feeds real documents into the prompt.',
        'The model answers from evidence — and you can cite the source.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Design **chunking strategies** for long-form documents and knowledge bases.',
        'Produce **embeddings**, store in a **vector index**, and query effectively.',
        'Build **grounded prompts** with citations back to source chunks.',
        'Wrap a RAG pipeline as **MCP tools** any agent can call.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'The RAG pipeline',
      icon: 'git-branch',
      points: [
        '**Ingest**: load documents, split into chunks, embed, store.',
        '**Retrieve**: user query → embed → vector search → top-k chunks.',
        '**Generate**: feed retrieved chunks + query to the LLM.',
        '**Cite**: link each claim in the answer back to its source chunk.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Chunking with overlap',
      code: `def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append({
            "text": chunk,
            "start": start,
            "end": min(end, len(text)),
            "index": len(chunks),
        })
        start += chunk_size - overlap
    return chunks`,
      highlights: [
        'Overlap prevents sentences from being cut in half between chunks',
        'Metadata (start, index) enables citation linking later',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Chunking strategies',
      icon: 'scissors',
      points: [
        '**Fixed window**: simple, predictable size. Good baseline.',
        '**Sentence-aware**: split on sentence boundaries inside the window.',
        '**Structure-aware**: honour headings, paragraphs, or log entry boundaries.',
        '**Overlap**: 10-20% overlap keeps context across boundaries.',
        'Smaller chunks = more precise retrieval; larger = more context per hit.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Embeddings — turning text into vectors',
      icon: 'compass',
      points: [
        'An embedding maps text to a fixed-length vector in semantic space.',
        'Similar meanings land **close together**; unrelated ones land far apart.',
        '**OpenAI** `text-embedding-3-small` — fast, cheap, 1536 dimensions.',
        '**Sentence Transformers** — local, free, great for prototyping.',
        'Always embed queries with the **same model** used for documents.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Embed and search',
      code: `from openai import OpenAI
import numpy as np

client = OpenAI()

def embed(texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(
        model="text-embedding-3-small", input=texts
    )
    return [d.embedding for d in resp.data]

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search(query, index, k=5):
    q_vec = embed([query])[0]
    scored = [(cosine_sim(q_vec, doc["vec"]), doc) for doc in index]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]`,
      highlights: [
        'Cosine similarity: 1.0 = identical direction, 0.0 = unrelated',
        'Real systems use FAISS or ChromaDB — same idea, much faster',
      ],
    },
  },
  // ---- Demo: Ingest + embed ----
  {
    type: 'title',
    content: {
      title: 'Demo — Ingest + embed',
      subtitle: 'Switch to terminal: python demo/ingest.py',
      icon: 'rocket',
    },
  },

  // ---- Section: Grounded generation ----
  {
    type: 'title',
    content: {
      title: 'Grounded generation',
      subtitle: 'Citations and knowing when to say "I don\'t know"',
      icon: 'book-open',
    },
  },

  {
    type: 'code',
    content: {
      title: 'Grounded prompt with citations',
      code: `def build_rag_prompt(query, chunks):
    context = "\\n\\n".join(
        f"[{c['index']}] {c['text']}" for c in chunks
    )
    return (
        f"Answer the question using ONLY the passages below.\\n"
        f"Cite passage numbers in square brackets.\\n\\n"
        f"Passages:\\n{context}\\n\\n"
        f"Question: {query}"
    )

# Answer: "The outage began at 14:32 UTC [2]
#          affecting the payments service [0]."`,
      highlights: [
        'Numbered passages let the model cite its sources',
        'ONLY constrains answers to retrieved evidence',
      ],
    },
  },

  // ---- Section: RAG as MCP tools ----
  {
    type: 'title',
    content: {
      title: 'RAG as MCP tools',
      subtitle: 'Make your pipeline a pluggable capability',
      icon: 'server',
    },
  },

  {
    type: 'standard',
    content: {
      title: 'Why wrap RAG in MCP?',
      icon: 'layers',
      points: [
        'The agent calls `search_docs` or `ask_docs` — it never touches embeddings or ChromaDB.',
        'Any MCP-compatible agent can use your RAG pipeline without code changes.',
        'The server owns the index lifecycle: build once at startup, serve many queries.',
        'Separation of concerns — swap the vector store without touching the agent.',
      ],
    },
  },

  {
    type: 'code',
    content: {
      title: 'FastMCP tool registration',
      code: `from mcp.server.fastmcp import FastMCP
from index_builder import load_logs, build_index, search

mcp = FastMCP("RAG Server")
logs = load_logs()
collection = build_index(logs)

@mcp.tool()
def search_docs(query: str, k: int = 5) -> str:
    """Search the document index for relevant passages."""
    hits = search(collection, query, k)
    return "\\n".join(
        f"[{h['id']}] (score {h['score']:.2f}) {h['text'][:200]}"
        for h in hits
    )`,
      highlights: [
        'Type hints generate JSON Schema — the agent discovers parameters automatically',
        'The index is built once at import time and shared across all tool calls',
      ],
    },
  },
  // ---- Demo: RAG MCP server ----
  {
    type: 'title',
    content: {
      title: 'Demo — RAG MCP server',
      subtitle: 'Switch to terminal: python demo/server.py',
      icon: 'rocket',
    },
  },
  // ---- Demo: RAG agent via MCP ----
  {
    type: 'title',
    content: {
      title: 'Demo — RAG agent via MCP',
      subtitle: 'Switch to terminal: python demo/agent.py',
      icon: 'rocket',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Field rules and exercises',
      icon: 'check-square',
    },
  },

  {
    type: 'rules',
    content: {
      title: 'Field rules — Module 5',
      rules: [
        {
          rule: 'Chunk for retrieval, not for reading',
          example: 'Smaller chunks with overlap beat whole-page dumps.',
          icon: 'scissors',
        },
        {
          rule: 'Same model for docs and queries',
          example: 'Mismatched embeddings produce garbage similarity scores.',
          icon: 'compass',
        },
        {
          rule: 'Always ground with citations',
          example: 'An answer without a source is just a hallucination with confidence.',
          icon: 'book-open',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — Build index: chunk, embed, and search with ChromaDB',
        '02 — RAG chat: grounded prompts with source citations',
        '03 — RAG MCP server: wrap the pipeline as tools for any agent',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 5 — Complete',
      subtitle: 'Next: structured facts and knowledge graphs',
      icon: 'check-circle',
    },
  },
];
