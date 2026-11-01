export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 13 — Edge Topics',
      subtitle: 'Advanced techniques: pick and choose',
      icon: 'sparkles',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'What this module covers',
      icon: 'compass',
      points: [
        'A **toolbox**, not a sequence — each topic stands alone, so pick what your system needs.',
        'Topics **1–11**: retrieval, grounding, safety and cost techniques — each with an exercise of the same number.',
        'Topics **12–14**: local ML on a laptop CPU — fine-tuning data, training, and running Hub models.',
        'Topics **15–18**: concepts to recognise — test-time compute, speculative decoding, GraphRAG, MoE.',
        'Evals (LLM-as-judge, retrieval metrics) have their own module — **Module 11**.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: '1. Hybrid Search',
      subtitle: 'Keyword + semantic retrieval',
      icon: 'search',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is hybrid search?',
      description:
        '**Hybrid search** is a retrieval technique that combines keyword and semantic search. It is used in RAG when users mix exact terms (product codes, names) with paraphrased questions. You run **BM25** and **vector** search in parallel, merge the ranked lists (often with RRF), and pass the top passages to the LLM. The result is one ranked list that catches both literal matches and meaning-based matches.',
      icon: 'search',
      credit:
        'Cormack, Clarke & Büttcher (2009). "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods." SIGIR.',
    },
  },
  {
    type: 'equation',
    content: {
      title: 'BM25 scoring',
      mathml: `<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">
  <mi>score</mi>
  <mo>(</mo>
  <mi>D</mi>
  <mo>,</mo>
  <mi>Q</mi>
  <mo>)</mo>
  <mo>=</mo>
  <munderover>
    <mo>&sum;</mo>
    <mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow>
    <mi>n</mi>
  </munderover>
  <mi>IDF</mi>
  <mo>(</mo>
  <msub><mi>q</mi><mi>i</mi></msub>
  <mo>)</mo>
  <mo>&#x22C5;</mo>
  <mfrac>
    <mrow>
      <mi>f</mi>
      <mo>(</mo><msub><mi>q</mi><mi>i</mi></msub><mo>,</mo><mi>D</mi><mo>)</mo>
      <mo>&#x22C5;</mo>
      <mo>(</mo><msub><mi>k</mi><mn>1</mn></msub><mo>+</mo><mn>1</mn><mo>)</mo>
    </mrow>
    <mrow>
      <mi>f</mi>
      <mo>(</mo><msub><mi>q</mi><mi>i</mi></msub><mo>,</mo><mi>D</mi><mo>)</mo>
      <mo>+</mo>
      <msub><mi>k</mi><mn>1</mn></msub>
      <mo>&#x22C5;</mo>
      <mrow>
        <mo>(</mo>
        <mn>1</mn><mo>&#x2212;</mo><mi>b</mi>
        <mo>+</mo>
        <mi>b</mi><mo>&#x22C5;</mo>
        <mfrac>
          <mrow><mo>|</mo><mi>D</mi><mo>|</mo></mrow>
          <mi>avgdl</mi>
        </mfrac>
        <mo>)</mo>
      </mrow>
    </mrow>
  </mfrac>
</math>`,
      description:
        'IDF weights rare terms higher. The fraction is term frequency with saturation (k₁ ≈ 1.5) — repeated terms give diminishing returns. b (≈ 0.75) normalises by document length so long docs are not unfairly boosted.',
    },
  },
  {
    type: 'equation',
    content: {
      title: 'Reciprocal Rank Fusion (RRF)',
      mathml: `<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">
  <mi>score</mi>
  <mo>(</mo>
  <mi>d</mi>
  <mo>)</mo>
  <mo>=</mo>
  <munderover>
    <mo>&sum;</mo>
    <mrow><mi>L</mi><mo>&isin;</mo><mi>lists</mi></mrow>
    <mrow></mrow>
  </munderover>
  <mfrac>
    <mn>1</mn>
    <mrow><mi>k</mi><mo>+</mo><mi>rank</mi><mo>(</mo><mi>d</mi><mo>,</mo><mi>L</mi><mo>)</mo></mrow>
  </mfrac>
</math>`,
      description:
        'For each document, sum 1/(k + rank) across all ranked lists. Documents high in both lists score highest. k is typically 60. Score-agnostic — no normalisation across BM25 and cosine scores.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Hybrid search',
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
    type: 'title',
    content: {
      title: '2. Re-ranking',
      subtitle: 'Precision after broad retrieval',
      icon: 'arrow-up-down',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is re-ranking?',
      description:
        '**Re-ranking** is a second pass that re-sorts search results for accuracy. It is used when initial retrieval returns many candidates but the order is unreliable. A **re-ranker** (usually a small cross-encoder, not your chat LLM) scores each passage together with the question. The best passages move to the top, then the LLM generates its answer from those — so the model sees the right context first.',
      icon: 'arrow-up-down',
      credit: 'Nogueira & Cho (2019). "Passage Re-ranking with BERT." arXiv:1901.04085',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Re-ranking',
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
    type: 'title',
    content: {
      title: '3. HyDE',
      subtitle: 'Hypothetical Document Embeddings',
      icon: 'lightbulb',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is HyDE?',
      description:
        "**HyDE** (Hypothetical Document Embeddings) is a retrieval trick for short or vague questions. It is used when the user's query looks nothing like the long documents in your index. The LLM writes a **hypothetical answer**, you embed that text, and search with that embedding instead of the raw question. Retrieval often improves because the fake answer sits closer to real passages in embedding space.",
      icon: 'lightbulb',
      credit:
        'Gao et al. (2022). "Precise Zero-Shot Dense Retrieval without Relevance Labels." arXiv:2212.10496',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'HyDE — Hypothetical Document Embeddings',
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
    type: 'title',
    content: {
      title: '4. Agentic RAG',
      subtitle: 'Retrieval as a tool',
      icon: 'bot',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is agentic RAG?',
      description:
        '**Agentic RAG** is RAG where the LLM decides if and when to search, instead of always retrieving up front. It is used for mixed questions (some need documents, some do not) and multi-step research. You expose search as a **tool**; the agent calls it, reads results, and may search again. The answer is built only from retrieved evidence when needed — no wasted context on simple queries.',
      icon: 'bot',
      credit:
        'Jiang et al. (2023). "Active Retrieval Augmented Generation." arXiv:2305.06983',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Agentic RAG',
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
    type: 'title',
    content: {
      title: '5. Citation Verification',
      subtitle: 'Grounding answers in evidence',
      icon: 'check-circle',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is citation verification?',
      description:
        '**Citation verification** is a post-generation check that grounds answers in sources. It is used when wrong or unsupported claims are unacceptable (legal, medical, finance). You **extract** claims from the answer, test each against retrieved passages, then flag or drop unsupported ones. The user gets an answer tied to evidence — or a refusal when the corpus does not support the claim.',
      icon: 'check-circle',
      credit:
        'Min et al. (2023). "FActScore: Fine-grained Atomic Evaluation of Factual Precision." arXiv:2305.14251',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Citation verification',
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
    type: 'title',
    content: {
      title: '6. Web Search Backend',
      subtitle: 'When the answer is not in your corpus',
      icon: 'globe',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is a web search backend?',
      description: 'A **web search backend** adds live internet search as a fallback retrieval source. It is used when users ask about things your index does not cover — current events, other products, general knowledge. You search internally first; if the best score is below a threshold, you query a web search API and normalise the results (title, snippet, URL) into the same passage format, so generation does not care where they came from.',
      icon: 'globe',
      credit: 'Nakano et al. (2021). "WebGPT: Browser-assisted question-answering with human feedback." arXiv:2112.09332',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Web search backend',
      icon: 'globe',
      points: [
        'Internal search first — your curated corpus stays the **authority**.',
        '**Fall back** to web search when the top internal score is below a threshold.',
        'Normalise web hits to the same `{text, source}` shape as internal passages.',
        'Trade-off: web results are unvetted, and add latency and an external dependency.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: '7. Text-to-SQL',
      subtitle: 'Natural language over structured data',
      icon: 'database',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is text-to-SQL?',
      description:
        '**Text-to-SQL** turns natural language into database queries. It is used when answers live in tables (sales, logs, inventory), not in documents. You give the LLM the **schema**; it writes a SELECT, you run it safely (read-only), then return rows or a plain-language summary. The user asks in English and gets data-backed answers without writing SQL.',
      icon: 'database',
      credit:
        'Yu et al. (2018). "Spider: A Large-Scale Human-Labeled Dataset for Complex Text-to-SQL." EMNLP.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Text-to-SQL',
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
    type: 'title',
    content: {
      title: '8. Advanced Guardrails',
      subtitle: 'Defence in depth for production',
      icon: 'shield',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What are advanced guardrails?',
      description:
        '**Guardrails** are safety checks on what goes into and out of your LLM. They are used in production to block abuse, redact secrets, and enforce output shape. You chain filters on **input** (toxic content, PII) and **output** (PII again, schema validation). Unsafe or malformed content is blocked or cleaned before the user sees it.',
      icon: 'shield',
      credit:
        'Inan et al. (2023). "Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations." arXiv:2312.06674',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Advanced guardrails',
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
    type: 'title',
    content: {
      title: '9. Semantic Caching',
      subtitle: 'Cache by meaning, not exact text',
      icon: 'zap',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is semantic caching?',
      description:
        '**Semantic caching** stores past LLM answers and reuses them for similar questions. It is used to cut cost and latency when many users ask the same thing in different words. You embed the new query, find a close match in the cache (by cosine similarity), and return the stored answer if similarity is high enough. Otherwise you call the LLM and add the new pair to the cache.',
      icon: 'zap',
      credit:
        'Bang et al. (2023). "GPTCache: An Open-Source Semantic Cache for LLM Applications." arXiv:2308.15179',
    },
  },
  {
    type: 'equation',
    content: {
      title: 'Cosine similarity',
      mathml: `<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">
  <mi>cos</mi>
  <mo>(</mo>
  <mi>a</mi>
  <mo>,</mo>
  <mi>b</mi>
  <mo>)</mo>
  <mo>=</mo>
  <mfrac>
    <mrow><mi>a</mi><mo>&sdot;</mo><mi>b</mi></mrow>
    <mrow><mo>|</mo><mi>a</mi><mo>|</mo><mo>|</mo><mi>b</mi><mo>|</mo></mrow>
  </mfrac>
</math>`,
      description:
        'Embed the incoming query, compare against cached query embeddings. If similarity exceeds a threshold (typically 0.95), return the cached response. Too low and you serve wrong answers; too high and the cache rarely hits.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Semantic caching',
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
    type: 'title',
    content: {
      title: '10. Multimodal RAG',
      subtitle: 'Images, diagrams, and text together',
      icon: 'image',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is multimodal RAG?',
      description:
        '**Multimodal RAG** retrieves from images and diagrams as well as text. It is used when manuals, scans, or product photos matter as much as written docs. At index time, a vision model **describes** each image in text; you embed those descriptions like normal chunks. At query time, search returns text and image-derived passages so the LLM can answer questions about visuals.',
      icon: 'image',
      credit:
        'Radford et al. (2021). "Learning Transferable Visual Models From Natural Language Supervision (CLIP)." ICML.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Multimodal RAG',
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
    type: 'title',
    content: {
      title: '11. Contextual Chunking',
      subtitle: 'How you split documents matters',
      icon: 'scissors',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is contextual chunking?',
      description:
        '**Contextual chunking** is how you split documents before indexing. It is used because bad splits break retrieval — sentences cut in half, topics split across chunks. You choose a strategy (fixed windows with overlap, parent-child sizes, or splits at topic boundaries), embed each chunk, and store metadata to link children to parents. Search hits precise chunks; generation can pull in the wider parent for context.',
      icon: 'scissors',
      credit:
        'Lewis et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Contextual chunking',
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
    type: 'title',
    content: {
      title: '12. DPO + LoRA',
      subtitle: 'Preference alignment + efficient training',
      icon: 'sliders',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is DPO?',
      description:
        '**DPO** (Direct Preference Optimization) is training that teaches a model which answers humans prefer. It is used for alignment — tone, safety, style — when prompting alone is not enough. You collect pairs of good vs bad responses and train with one preference loss (no separate reward model). Usually you use **LoRA** so only small adapter weights change. The model learns to favour the chosen style on similar prompts.',
      icon: 'sliders',
      credit:
        'Rafailov et al. (2023). "Direct Preference Optimization: Your Language Model is Secretly a Reward Model." NeurIPS 2023.',
    },
  },
  {
    type: 'equation',
    content: {
      title: 'LoRA — Low-Rank Adaptation',
      mathml: `<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">
  <msup><mi>W</mi><mo>&#8242;</mo></msup>
  <mo>=</mo>
  <mi>W</mi>
  <mo>+</mo>
  <mi>B</mi>
  <mi>A</mi>
</math>`,
      description:
        'Instead of updating all weights W, LoRA adds small trainable matrices B and A. W′ = W + BA. This is how DPO and other fine-tunes run efficiently — gigabytes of GPU memory, not terabytes.',
      credit:
        'Hu et al. (2021). "LoRA: Low-Rank Adaptation of Large Language Models." ICLR 2022.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'DPO + LoRA',
      icon: 'sliders',
      points: [
        '**RLHF**: policy + reward + reference models, PPO optimisation loop.',
        '**DPO**: one loss on (chosen, rejected) preference pairs.',
        '**LoRA**: train only B and A adapters — same alignment, far less memory.',
        'Standard pipeline for open-source preference fine-tunes (Mixtral, Llama).',
        'Exercise `12-fine-tuning-data`: prepare the chat JSONL a fine-tune needs.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: '13. Train a Model Locally',
      subtitle: 'CPU only — no GPU required',
      icon: 'cpu',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is local training?',
      description:
        '**Local training** means updating a small neural network on your own machine instead of calling a cloud API. It is used when you have labelled examples and want a cheap, repeatable classifier (intent, urgency, department). You prepare text + label pairs, fine-tune a base model like DistilBERT with Hugging Face **Trainer**, save weights to disk, then call **predict** on new text. You end up with a model file you own — no API key at inference time.',
      icon: 'cpu',
      credit:
        'Wolf et al. (2020). "Transformers: State-of-the-Art Natural Language Processing." EMNLP System Demonstrations.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Local training workflow',
      icon: 'cpu',
      points: [
        'Install: `pip install -e ".[local-ml]"` (~2–4 GB RAM on CPU).',
        'Prepare labelled JSON: `{text, label}` pairs (demo: urgent/routine; exercise: department).',
        'Tokenise → **Trainer** with `max_steps=30` → save to `models/`.',
        'First run downloads **distilbert-base-uncased** (~250MB).',
        'Demo: `python demo/13_train_local.py` · Exercise: `exercises/13-local-training/`',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — Local training',
      subtitle: 'python module-13-edge-topics/demo/13_train_local.py',
      icon: 'rocket',
    },
  },
  {
    type: 'title',
    content: {
      title: '14. Run a Hugging Face Model',
      subtitle: 'Download once, run on CPU',
      icon: 'package',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is running a Hub model?',
      description:
        'The **Hugging Face Hub** hosts thousands of pre-trained models you download and run locally. It is used when you need a capability (sentiment, classification, translation) without training from scratch. You load a model id (e.g. DistilBERT fine-tuned on reviews), pass text through a **pipeline** or tokenizer + model, and read scores or labels. The model stays on disk in a cache — later runs start instantly.',
      icon: 'package',
      credit:
        'Lhoest et al. (2021). "Datasets: A Community Library for Natural Language Processing." NeurIPS.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Hugging Face run workflow',
      icon: 'package',
      points: [
        'Install: `pip install -e ".[local-ml]"`.',
        'Demo: **`pipeline("sentiment-analysis")`** on ship logs — fastest path.',
        'Exercise: **AutoTokenizer** + **AutoModel** + softmax — see what the pipeline hides.',
        'Model: `distilbert-base-uncased-finetuned-sst-2-english` (~250MB download).',
        'Demo: `python demo/14_huggingface_run.py` · Exercise: `exercises/14-huggingface-run/`',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Small models to try on CPU',
      icon: 'package',
      points: [
        '`distilbert-base-uncased-finetuned-sst-2-english` — sentiment (66M, ~250MB).',
        '`cardiffnlp/twitter-roberta-base-sentiment-latest` — 3-class sentiment (125M, ~500MB).',
        '`sentence-transformers/all-MiniLM-L6-v2` — sentence embeddings (22M, ~90MB).',
        '`facebook/bart-large-mnli` — zero-shot classification (407M, ~1.6GB).',
        '`Helsinki-NLP/opus-mt-en-fr` — English→French translation (74M, ~300MB).',
        '`google/flan-t5-small` — instruction-tuned text generation (77M, ~300MB).',
        'Rule of thumb: <500M params, "base"/"small"/"distil"/"mini" in the name → fine on CPU.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — Hugging Face run',
      subtitle: 'python module-13-edge-topics/demo/14_huggingface_run.py',
      icon: 'rocket',
    },
  },
  {
    type: 'title',
    content: {
      title: '15. Test-Time Compute Scaling',
      subtitle: 'Think longer, not bigger',
      icon: 'brain',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is test-time compute scaling?',
      description:
        'Normally an LLM answers in **one shot**: your question goes in, tokens come out. **Test-time compute scaling** means the model uses **more work at answer time** — extra tokens, steps, or attempts before you see the final reply. It is used for hard problems (math, logic, planning) where a quick first guess is often wrong. The system might write hidden reasoning, try several approaches, or check its own draft — like giving the model more exam time, not a bigger brain. You pay more latency and cost per question; you often get a better answer.',
      icon: 'brain',
      credit:
        'Snell et al. (2024). "Scaling LLM Test-Time Compute Optimally." arXiv:2408.03314',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Test-time compute scaling',
      icon: 'brain',
      points: [
        '**Train-time**: make the model bigger (more parameters, more GPU weeks).',
        '**Test-time**: same model, but **more inference steps** per user question.',
        'Examples: chain-of-thought, self-check, multiple samples + pick best (o1, DeepSeek-R1).',
        'Trade-off: answers can improve a lot; each query costs more time and money.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: '16. Speculative Decoding',
      subtitle: 'Draft fast, verify once',
      icon: 'zap',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is speculative decoding?',
      description: '**Speculative decoding** speeds up generation without changing the output. A small, fast **draft** model proposes several tokens; the large model checks them all in one forward pass and keeps the ones it agrees with. It is used in production serving where latency matters. Accepted tokens arrive in bulk — typically **2–4× faster** — and the final text is distributed exactly as if the large model had written it alone.',
      icon: 'zap',
      credit: 'Leviathan, Kalman & Matias (2023). "Fast Inference from Transformers via Speculative Decoding." ICML.',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Speculative decoding',
      icon: 'zap',
      points: [
        'Draft model guesses **k tokens**; target model verifies them in **one pass**.',
        'Keep the agreed prefix, resample at the first mismatch, repeat.',
        'Same output distribution as the large model — only faster.',
        'Trade-off: memory for a second model; more complex serving stack.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: '17. GraphRAG',
      subtitle: 'Knowledge graphs meet retrieval',
      icon: 'share-2',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is GraphRAG?',
      description:
        '**GraphRAG** is retrieval built on a knowledge graph, not just vector chunks. It is used for corpus-wide questions ("what are the main themes across these reports?"). You extract entities and links, group them into communities, and pre-summarise each cluster. A query can hit local chunks *or* those cluster summaries. You get both precise facts and big-picture answers.',
      icon: 'share-2',
      credit:
        'Edge et al. (2024). "From Local to Global: A Graph RAG Approach to Query-Focused Summarization." arXiv:2404.16130',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'GraphRAG',
      icon: 'share-2',
      points: [
        'Extract entities + relationships → build a **knowledge graph**.',
        '**Community detection** + pre-summarise each cluster.',
        'Global queries answered at the cluster level, not chunk level.',
        'Combines local vector precision with global understanding.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: '18. Mixture of Experts',
      subtitle: 'Massive parameters, selective compute',
      icon: 'layers',
    },
  },
  {
    type: 'description',
    content: {
      title: 'What is a Mixture of Experts model?',
      description:
        'A **Mixture of Experts (MoE)** model has many specialist sub-networks but only runs a few per token. It is used to build very capable models without paying the full cost of every parameter on every token. A **router** picks top-K experts for each token; the rest stay idle. You get large-model quality with smaller active compute — e.g. Mixtral activates ~13B of ~47B parameters per token.',
      icon: 'layers',
      credit: 'Jiang et al. (2024). "Mixtral of Experts." arXiv:2401.04088',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Mixture of Experts',
      icon: 'layers',
      points: [
        'Each block has **N expert** feed-forward layers instead of one.',
        'A learned **router** picks top-K experts per token.',
        'Mixtral 8×7B: ~47B total params, ~13B active per token.',
        'GPT-4 is widely believed to use MoE for scale and cost.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Choosing techniques for your system',
      icon: 'puzzle',
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
          'Evaluation (Module 11)',
          'Guardrails',
          'Good chunking strategy',
        ],
      },
      right: {
        label: 'Use when needed',
        items: [
          'HyDE (specialised domains)',
          'GraphRAG (global / thematic queries)',
          'DPO + LoRA (preference alignment)',
          'Test-time compute (hard reasoning)',
          'Speculative decoding (latency)',
          'MoE awareness (model selection)',
          'Web search (out-of-corpus questions)',
          'Text-to-SQL (structured data)',
          'Semantic caching (high traffic)',
          'Multimodal (images in corpus)',
        ],
      },
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises — 14 hands-on topics',
      points: [
        '01–05: Hybrid search, re-ranking, HyDE, agentic RAG, citation verification',
        '06–07: Web search backend, text-to-SQL',
        '08–11: Advanced guardrails, semantic cache, multimodal RAG, contextual chunking',
        '12–14: Fine-tuning data prep, **local training (CPU)**, **Hugging Face run**',
        'Exercise numbers match topic numbers. Topics 15–18 are concepts only.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Capstone projects',
      subtitle: 'extras/ — choose one, build it production-ready',
      icon: 'pen-tool',
    },
  },
  {
    type: 'cards',
    content: {
      title: 'Pick your capstone',
      cards: [
        {
          heading: 'AI Recipe Finder',
          points: [
            'Photo your fridge, get recipe suggestions.',
            'RAG + hybrid search + multimodal vision.',
            'Allergen guardrails + semantic caching.',
          ],
        },
        {
          heading: 'AI Movie Night',
          points: [
            'Describe your mood, get movie picks.',
            'RAG + reranking + text-to-SQL for data questions.',
            'Charts and structured output.',
          ],
        },
        {
          heading: 'AI Travel Planner',
          points: [
            'Describe your dream trip, get a day-by-day itinerary.',
            'Agentic RAG + tool calling + web fallback.',
            'Budget tracking + structured itineraries.',
          ],
        },
        {
          heading: 'AI Personal Assistant',
          points: [
            'Friendly companion with calendar, notes, reminders.',
            'Chat + tool calling + MCP + RAG over notes.',
            'Session memory + cost controls.',
          ],
        },
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'How the capstones work',
      icon: 'pen-tool',
      points: [
        'Each capstone in **`extras/`** has a **frontend/** (SvelteKit — provided), a **starter/** (your code), and a **solution/**.',
        'You build the **FastAPI backend** in `starter/` — the frontend connects automatically.',
        'Combine **Module 12** patterns (tracing, retries, cost tracking) with **Module 13** techniques (hybrid search, caching, guardrails).',
        'Run with `uvicorn starter.app:app --reload --port 8000` and `cd frontend && pnpm dev`.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 13 — Complete',
      subtitle: 'Next: pick a capstone in extras/',
      icon: 'check-circle',
    },
  },
];
