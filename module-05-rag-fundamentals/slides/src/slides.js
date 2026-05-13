export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 5 — RAG Fundamentals',
      subtitle: 'Ground answers in ship knowledge, not guesses',
      icon: 'book-open',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Why RAG?',
      points: [
        'LLMs hallucinate. Ship logs do not.',
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
        'Design **chunking strategies** for long-form ship logs and manuals.',
        'Produce **embeddings**, store in a **vector index**, and query effectively.',
        'Apply **retrieval strategies**: hybrid search, filters, reranking.',
        'Build **grounded prompts** with citations back to source chunks.',
        'Evaluate RAG with **recall**, **precision**, and adversarial queries.',
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
  {
    type: 'comparison',
    content: {
      title: 'Dense vs sparse retrieval',
      left: {
        label: 'Dense (vector)',
        items: [
          'Understands meaning and synonyms',
          'Needs an embedding model',
          'Great for natural-language questions',
          'Misses exact terms (serial numbers)',
        ],
      },
      right: {
        label: 'Sparse (keyword / BM25)',
        items: [
          'Exact term matching',
          'No model needed — fast and simple',
          'Great for codes, IDs, error strings',
          'Misses paraphrases and synonyms',
        ],
      },
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Hybrid search and reranking',
      icon: 'layers',
      points: [
        '**Hybrid**: run both dense and sparse, merge results.',
        '**Reciprocal rank fusion (RRF)**: combine ranked lists without scores.',
        '**Reranker**: a cross-encoder rescores the top-N for better precision.',
        '**Metadata filters**: narrow by date, author, department before search.',
      ],
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

# Answer: "The hull breach occurred on deck 7 [2]
#          during the Kepler Sweep [0]."`,
      highlights: [
        'Numbered passages let the model cite its sources',
        'ONLY constrains answers to retrieved evidence',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Evaluating RAG',
      icon: 'check-square',
      points: [
        '**Retrieval recall**: are the right chunks in the top-k?',
        '**Retrieval precision**: are irrelevant chunks polluting the context?',
        '**Answer faithfulness**: does the answer stick to retrieved evidence?',
        '**Adversarial tests**: questions with no answer in the corpus.',
        'A RAG system that says "I don\'t know" when it shouldn\'t guess is a good system.',
      ],
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
      title: 'Exercises — Mining the ship archives',
      points: [
        '01 — Document chunker: split ship logs into overlapping windows',
        '02 — Vector search: embed and search the mission archives',
        '03 — RAG pipeline: end-to-end retrieval with citation linking',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Archives online — Module 5',
      subtitle: 'The ship has memory now. Next: give it colleagues.',
      icon: 'party-popper',
    },
  },
];
