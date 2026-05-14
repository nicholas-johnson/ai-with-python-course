export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 11 — Edge Topics',
      subtitle: 'Advanced techniques: pick and choose',
      icon: 'sparkles',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'A toolbox, not a pipeline',
      points: [
        'These 13 topics are **independent** — pick based on interest and time.',
        'Some you will use on every production system (hybrid search, re-ranking).',
        'Others are situational but powerful when the need arises (fine-tuning, multimodal).',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '1. Hybrid search',
      icon: 'search',
      points: [
        'Combine **BM25** (keyword) and **vector** (semantic) search.',
        'Reciprocal Rank Fusion (RRF) merges ranked lists: `1/(k + rank)`.',
        'Score-agnostic — no normalisation needed across different scoring functions.',
        'Consistently outperforms either approach alone on real-world queries.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '2. Re-ranking',
      icon: 'arrow-up-down',
      points: [
        'Initial retrieval is optimised for **recall**, not precision.',
        'Re-rank top-N with a **cross-encoder** or **LLM scorer**.',
        'Scores each (query, passage) pair together — catches nuance.',
        'Pipeline: retrieve 50 → re-rank 20 → generate from top 5.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '3. HyDE — Hypothetical Document Embeddings',
      icon: 'lightbulb',
      points: [
        'Short queries land far from detailed documents in embedding space.',
        'Generate a **hypothetical answer** first, embed that instead.',
        'The hypothetical doc is structurally closer to real documents.',
        'Works best for knowledge-intensive domains with specialised vocab.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '4. Agentic RAG',
      icon: 'bot',
      points: [
        'Standard RAG: fixed retrieval step for every query.',
        'Agentic RAG: the LLM **decides** whether, when, and what to retrieve.',
        'Retrieval is a **tool** the agent calls on demand.',
        'Handles multi-hop questions and skips retrieval when unnecessary.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '5. Citation verification',
      icon: 'check-circle',
      points: [
        'LLMs generate plausible claims not backed by sources.',
        '**Extract** individual claims → **check** each against passages.',
        'Flag or remove **unsupported** claims before returning to user.',
        'Essential for high-stakes domains (legal, medical, financial).',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '6. Web search backend',
      icon: 'globe',
      points: [
        'Internal knowledge bases have limited scope.',
        'Add **live web search** as a fallback retrieval source.',
        'DuckDuckGo (free) or Bing/Google APIs (production).',
        'Normalise web results into the same format as internal documents.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '7. Text-to-SQL',
      icon: 'database',
      points: [
        'Not all data lives in documents — much sits in **databases**.',
        'Inject the schema into the prompt; the LLM generates SELECT queries.',
        '**Safety**: read-only connections, forbidden keyword validation.',
        'Summarise results in natural language for better UX.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '8. Eval / LLM-as-judge',
      icon: 'bar-chart',
      points: [
        'You cannot improve what you cannot **measure**.',
        'Evaluate: **retrieval** quality (precision, recall) + **generation** quality.',
        'LLM-as-judge scores correctness, completeness, relevance, faithfulness.',
        'Build a test set of 50-100 QA pairs; track scores over time.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '9. Fine-tuning basics',
      icon: 'settings',
      points: [
        'When prompting plateaus: **fine-tune** on your examples.',
        'LoRA/QLoRA: parameter-efficient, feasible on consumer hardware.',
        'Data quality beats quantity — 100 excellent > 10,000 mediocre.',
        'Today: data preparation only (actual training is too slow for workshops).',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '10. Advanced guardrails',
      icon: 'shield',
      points: [
        '**Content filtering**: block toxic, harmful, or off-topic I/O.',
        '**PII detection**: redact emails, phone numbers, SSNs.',
        '**Schema validation**: Pydantic models enforce output structure.',
        'Defence in depth: chain multiple layers; no single guardrail is perfect.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '11. Semantic caching',
      icon: 'zap',
      points: [
        'Traditional caching needs exact key match — misses paraphrases.',
        'Semantic cache: embed query → find similar cached queries → return response.',
        'Similarity threshold (0.95) controls hit/miss sensitivity.',
        'Can serve 30-60% of queries from cache in repetitive workloads.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '12. Multimodal RAG',
      icon: 'image',
      points: [
        'Knowledge bases contain **images**, diagrams, charts alongside text.',
        'Vision model generates text descriptions → embed → store in vector DB.',
        'Search returns both text chunks and image descriptions.',
        'Generate answers referencing both text and visual sources.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: '13. Contextual chunking',
      icon: 'scissors',
      points: [
        'How you chunk has **massive** impact on retrieval quality.',
        '**Parent-child**: small chunks for search, large parents for context.',
        '**Overlapping windows**: redundancy at chunk boundaries.',
        '**Semantic chunking**: split at natural topic boundaries.',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'When to use what',
      left: {
        label: 'Always use',
        items: [
          'Hybrid search',
          'Re-ranking',
          'Evaluation',
          'Guardrails',
          'Good chunking strategy',
        ],
      },
      right: {
        label: 'Use when needed',
        items: [
          'HyDE (specialised domains)',
          'Fine-tuning (prompting plateaus)',
          'Multimodal (images in corpus)',
          'Text-to-SQL (structured data)',
          'Semantic caching (high traffic)',
        ],
      },
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — 13 standalone topics',
      points: [
        '01-05: Hybrid search, re-ranking, HyDE, agentic RAG, citation verification',
        '06-09: Web search, text-to-SQL, LLM eval, fine-tuning data prep',
        '10-13: Guardrails, semantic caching, multimodal RAG, contextual chunking',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Edge Topics — Module 11',
      subtitle: 'Your advanced toolbox is ready. Build something great.',
      icon: 'rocket',
    },
  },
];
