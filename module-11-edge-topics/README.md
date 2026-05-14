# Module 11 — Edge Topics

This is a collection of advanced and emerging techniques that push beyond the core RAG and agent patterns covered in earlier modules. Unlike other modules, these topics are **independent** — pick and choose based on interest and time. Each has a standalone exercise that can be completed in any order.

Think of this module as a toolbox of specialised techniques. Some (hybrid search, re-ranking) you will use on almost every production system. Others (fine-tuning, multimodal RAG) are situational but powerful when the need arises. All of them are worth understanding at a conceptual level so you know what to reach for when the time comes.

---

## 1. Hybrid Search

### Concept

Pure vector search finds semantically similar documents but can miss exact keyword matches. A query for "error code FTL-4092" may not surface the one document containing that code because the embedding captures meaning, not tokens. Conversely, pure keyword search (BM25) excels at exact matches but fails when the user paraphrases or asks conceptually.

Hybrid search combines both approaches. You run a vector search and a keyword (BM25) search in parallel, then merge the two ranked lists into a single result. The standard merging technique is **Reciprocal Rank Fusion (RRF)**: for each document, you sum `1 / (k + rank)` across all lists, where `k` is a constant (typically 60). Documents that appear high in both lists get the highest fused score.

The beauty of RRF is that it is score-agnostic — you do not need to normalise BM25 scores against cosine similarities. It operates purely on rank positions, which makes it robust across different scoring functions. In practice, hybrid search consistently outperforms either approach alone, especially on real-world queries that mix specific terminology with conceptual intent.

The main trade-off is complexity: you maintain two indexes (vector and keyword) and run two searches per query. For most production systems this is a worthwhile cost, but for simple prototypes a single vector search is often sufficient.

### Code Pattern

```python
def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### When to Use

- Almost always in production RAG systems.
- When queries mix specific terms (names, codes, dates) with semantic intent.
- Trade-off: two indexes to maintain, slightly higher latency per query.

---

## 2. Re-ranking

### Concept

Initial retrieval (whether vector, keyword, or hybrid) is optimised for recall — casting a wide net to avoid missing relevant documents. But the ranking within those results is often imprecise because the retrieval model encodes the query and each document independently (bi-encoder), missing fine-grained interactions between them.

A re-ranker applies a more expensive but more accurate model to the top-N results. Cross-encoders process the (query, document) pair together, attending to every token interaction. This catches nuances like negation, qualification, and subtle relevance that bi-encoders miss. An LLM-based re-ranker takes this further by using an instruction-tuned model to score relevance on a scale, with the ability to reason about whether a passage actually answers the question.

The typical pipeline is: retrieve 50-100 candidates cheaply, re-rank the top 20-30 with a cross-encoder or LLM, then pass the top 5-10 to generation. This two-stage approach gives you the speed of bi-encoder retrieval with the precision of cross-encoder scoring.

The trade-off is latency and cost. Cross-encoders are O(n) in the number of candidates, and LLM-based re-rankers consume tokens for each candidate. Keep the candidate set small (under 30) and the re-ranker adds only 200-500ms.

### Code Pattern

```python
from openai import OpenAI

def rerank_with_llm(
    client: OpenAI,
    query: str,
    passages: list[dict],
    top_k: int = 5,
) -> list[dict]:
    scored = []
    for passage in passages:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": (
                    f"Rate the relevance of this passage to the query "
                    f"on a scale of 0-10.\n\n"
                    f"Query: {query}\n\n"
                    f"Passage: {passage['text']}\n\n"
                    f"Respond with just a number."
                ),
            }],
        )
        score = float(response.choices[0].message.content.strip())
        scored.append({**passage, "rerank_score": score})
    scored.sort(key=lambda x: x["rerank_score"], reverse=True)
    return scored[:top_k]
```

### When to Use

- When retrieval quality matters more than latency (knowledge-intensive QA, legal, medical).
- After hybrid search to refine the top candidates.
- Trade-off: adds latency per candidate; LLM re-ranking also adds cost.

---

## 3. Query Expansion / HyDE

### Concept

When a user asks a question, the query embedding may not land close to the relevant document embeddings in vector space. This is the **query-document mismatch** problem: questions are short and abstract while documents are long and detailed. Hypothetical Document Embeddings (HyDE) solves this by generating a hypothetical answer first, then embedding that answer instead of the original query.

The insight is that a generated answer — even if factually wrong — is structurally and semantically closer to real documents than the original question is. If someone asks "What are the effects of radiation on hull integrity?", the LLM generates a paragraph about radiation damage, material degradation, and structural weakening. This hypothetical document, when embedded, lands closer to actual reports about hull integrity than the short question would.

The pipeline is: (1) generate a hypothetical answer using the LLM, (2) embed the hypothetical answer, (3) search the vector store with that embedding. You can also average the original query embedding with the hypothetical document embedding for a balanced approach.

HyDE works best for knowledge-intensive queries where the vocabulary gap between questions and documents is large. It is less useful for simple factual lookups where the query already contains the key terms.

### Code Pattern

```python
from openai import OpenAI

def hyde_search(client: OpenAI, query: str, collection) -> list:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Write a short paragraph that answers this question. "
                f"It does not need to be factually correct — just write "
                f"what a good answer would look like.\n\n"
                f"Question: {query}"
            ),
        }],
    )
    hypothetical_doc = response.choices[0].message.content
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=hypothetical_doc,
    )
    results = collection.query(
        query_embeddings=[embedding.data[0].embedding],
        n_results=5,
    )
    return results
```

### When to Use

- Knowledge-intensive domains with specialised vocabulary (science, legal, medical).
- When queries are short/abstract but documents are detailed.
- Trade-off: extra LLM call per query; the hypothetical document can mislead if the LLM hallucinates in the wrong direction.

---

## 4. Agentic RAG

### Concept

In a standard RAG pipeline, retrieval is a fixed step: every query triggers a search, the results are stuffed into context, and the LLM generates an answer. This is wasteful when the question does not require retrieval ("What is 2 + 2?") and insufficient when the question requires multiple rounds of retrieval ("Compare the maintenance logs from January and March").

Agentic RAG gives the LLM the ability to decide whether, when, and what to retrieve. Retrieval becomes a tool that the agent calls on demand, just like a calculator or a code interpreter. The agent reasons about the query, decides if it needs external information, formulates a search query (which may differ from the user's question), evaluates the results, and decides whether to search again or answer.

This pattern naturally handles multi-hop questions: the agent retrieves information about topic A, discovers it needs to know about topic B, searches again, and synthesises both results. It also handles questions that need no retrieval at all, avoiding unnecessary context stuffing.

The implementation is straightforward with tool-use APIs. Define a `search_documents` tool with a description that helps the LLM understand when to use it. The agent's system prompt should encourage it to think about what information it needs before acting.

### Code Pattern

```python
from openai import OpenAI
import json

tools = [{
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "Search the document database for relevant information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documents.",
                }
            },
            "required": ["query"],
        },
    },
}]

def agentic_rag(client: OpenAI, question: str, search_fn) -> str:
    messages = [
        {"role": "system", "content": "Answer questions using the search tool when needed."},
        {"role": "user", "content": question},
    ]
    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=tools,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                results = search_fn(args["query"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(results),
                })
        else:
            return msg.content
```

### When to Use

- Multi-hop questions requiring iterative retrieval.
- Mixed workloads where some queries need retrieval and others do not.
- Trade-off: more LLM calls per query; agent may over-retrieve or under-retrieve without good prompting.

---

## 5. Citation Verification

### Concept

LLMs can generate plausible-sounding claims that are not actually supported by the retrieved passages. This is especially dangerous in domains where accuracy matters (legal, medical, financial). Citation verification adds a post-generation step that checks whether each claim in the answer is backed by the evidence.

The verification process works in three stages: (1) extract individual claims from the generated answer, (2) for each claim, check whether any retrieved passage supports it, (3) flag or remove unsupported claims. The checking can be done by an LLM that receives the claim and each passage and returns a support verdict (supported, partially supported, unsupported).

A strict system rejects answers containing any unsupported claims and either regenerates or returns "I don't have enough information." A lenient system annotates claims with their support status, letting the user decide what to trust. Most production systems fall somewhere in between — they flag unsupported claims with a warning while presenting supported ones with source citations.

This pattern is essential for any system where hallucination has real consequences. The overhead is modest: one additional LLM call per claim-passage pair, though you can batch these for efficiency.

### Code Pattern

```python
from openai import OpenAI

def verify_claims(
    client: OpenAI,
    answer: str,
    passages: list[str],
) -> list[dict]:
    claims = extract_claims(client, answer)
    results = []
    for claim in claims:
        supported = False
        supporting_passage = None
        for passage in passages:
            verdict = check_support(client, claim, passage)
            if verdict == "supported":
                supported = True
                supporting_passage = passage
                break
        results.append({
            "claim": claim,
            "supported": supported,
            "source": supporting_passage,
        })
    return results

def extract_claims(client: OpenAI, answer: str) -> list[str]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Extract each factual claim as a separate line:\n\n{answer}",
        }],
    )
    return [c.strip() for c in response.choices[0].message.content.split("\n") if c.strip()]
```

### When to Use

- High-stakes domains: legal, medical, financial, compliance.
- Any system that presents AI-generated information as factual.
- Trade-off: additional latency and cost for verification; can be overly strict on paraphrased information.

---

## 6. Web Search Backend

### Concept

Your internal knowledge base has a fixed scope — it only knows what you have indexed. When a user asks about current events, competitor products, or topics outside your corpus, vector search returns low-relevance results and the LLM either hallucinates or gives a generic "I don't know."

A web search backend adds live internet search as a fallback retrieval source. When internal search scores are below a confidence threshold, or when the query is explicitly about external information, the system dispatches the query to a web search API. The results (titles, snippets, URLs) are formatted as passages and fed to the LLM just like internal documents.

DuckDuckGo provides a free, no-API-key search option via its HTML interface. For production use, Bing Search API, Google Custom Search, or Brave Search offer structured JSON responses with better reliability. The key implementation detail is normalising web results into the same format as internal results so the generation step does not need to know the source.

You can combine web search with internal search using hybrid strategies: always search both and merge, or search internally first and fall back to web only when confidence is low. The latter approach preserves the authority of your curated knowledge base while providing a safety net for out-of-scope queries.

### Code Pattern

```python
import httpx
from urllib.parse import quote_plus

def web_search(query: str, max_results: int = 5) -> list[dict]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = httpx.get(url, headers=headers, follow_redirects=True)
    results = parse_duckduckgo_html(response.text)
    return results[:max_results]

def search_with_fallback(query, vector_search_fn, threshold=0.7):
    internal_results = vector_search_fn(query)
    if internal_results and internal_results[0]["score"] >= threshold:
        return {"source": "internal", "results": internal_results}
    web_results = web_search(query)
    return {"source": "web", "results": web_results}
```

### When to Use

- When your knowledge base has limited scope and users ask varied questions.
- Current events, competitor analysis, general knowledge queries.
- Trade-off: web results are unvetted (may contain misinformation); adds external dependency and latency.

---

## 7. Text-to-SQL

### Concept

Not all data lives in documents — much of it sits in relational databases. Text-to-SQL lets users query structured data with natural language. The LLM receives the database schema (table names, columns, types, relationships) and generates a SQL query that answers the user's question.

The key to reliable text-to-SQL is schema injection: include the full schema (or relevant portions) in the prompt so the LLM knows what tables and columns exist. Without this, the model guesses at table names and generates invalid SQL. For large databases, use schema filtering — select only the tables relevant to the query.

Safety is critical. Never execute LLM-generated SQL with write permissions. Use read-only database connections, parameterised queries where possible, and query validation (no DROP, DELETE, UPDATE). Some systems add a verification step where the LLM checks its own SQL for correctness before execution.

The results come back as structured rows, which you can either return directly or feed to the LLM for natural-language summarisation. The latter is usually better UX — "The average response time in January was 3.2 seconds" reads better than a raw table.

### Code Pattern

```python
import sqlite3
from openai import OpenAI

def text_to_sql(client: OpenAI, question: str, schema: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                f"Generate a SQLite SELECT query for the question. "
                f"Return ONLY the SQL, no explanation.\n\nSchema:\n{schema}"
            )},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content.strip().strip("```sql").strip("```").strip()

def safe_execute(db_path: str, sql: str) -> list[dict]:
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    if any(word in sql.upper() for word in forbidden):
        raise ValueError(f"Unsafe SQL detected: {sql}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

### When to Use

- Structured data: analytics dashboards, inventory, logs, metrics.
- When users need to query databases without knowing SQL.
- Trade-off: SQL injection risk requires careful sandboxing; complex joins and subqueries may fail.

---

## 8. Eval / LLM-as-Judge

### Concept

You cannot improve what you cannot measure. Evaluation of RAG systems has two dimensions: retrieval quality (did we find the right documents?) and generation quality (did the LLM produce a correct, faithful answer?). Traditional metrics like BLEU and ROUGE compare surface-level text overlap, but LLM-as-judge evaluators can assess semantic correctness, faithfulness to sources, and relevance to the question.

Retrieval quality is measured with precision (what fraction of retrieved documents are relevant?) and recall (what fraction of relevant documents were retrieved?). You need a labelled dataset with known relevant documents per query. For generation quality, the key dimensions are: **faithfulness** (is every claim supported by the context?), **relevance** (does the answer address the question?), and **completeness** (does it cover all aspects?).

LLM-as-judge works by prompting a strong model to evaluate an answer against a reference or against the retrieved context. The judge receives the question, the candidate answer, and optionally a reference answer, then scores on specified dimensions. To reduce bias, use structured rubrics, multiple evaluation dimensions, and consider running the judge multiple times to average scores.

The practical workflow is: build a test set of 50-100 question-answer pairs, run your RAG pipeline on each question, then evaluate with the LLM judge. Track scores over time as you iterate on prompts, retrieval strategies, and chunking.

### Code Pattern

```python
from openai import OpenAI

def llm_judge(
    client: OpenAI,
    question: str,
    answer: str,
    reference: str,
) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": (
                f"Evaluate this answer against the reference.\n\n"
                f"Question: {question}\n\n"
                f"Answer: {answer}\n\n"
                f"Reference: {reference}\n\n"
                f"Score each dimension 1-5:\n"
                f"- Correctness: Is the answer factually correct?\n"
                f"- Completeness: Does it cover all key points?\n"
                f"- Relevance: Does it address the question?\n\n"
                f"Respond as JSON: {{\"correctness\": N, \"completeness\": N, \"relevance\": N, \"explanation\": \"...\"}}"
            ),
        }],
    )
    return json.loads(response.choices[0].message.content)
```

### When to Use

- Every production RAG system should have evaluation.
- During development to compare prompt/retrieval strategies.
- Trade-off: LLM judges have their own biases; use structured rubrics and multiple dimensions.

---

## 9. Fine-tuning Basics

### Concept

Prompt engineering gets you far, but sometimes the model needs to learn patterns that are hard to express in a prompt: specific output formats, domain jargon, consistent tone, or nuanced classification boundaries. Fine-tuning trains the model on your examples so these patterns become built-in rather than instructed.

The modern approach to fine-tuning uses parameter-efficient methods like LoRA (Low-Rank Adaptation) or QLoRA (quantised LoRA). Instead of updating all model weights, LoRA adds small trainable matrices to attention layers. This reduces memory requirements from hundreds of gigabytes to a few gigabytes, making fine-tuning feasible on consumer hardware. QLoRA goes further by quantising the base model to 4-bit precision.

Data preparation is the most important step. You need high-quality input-output pairs in the format the model expects (typically JSONL with messages arrays). Quality beats quantity — 100 excellent examples often outperform 10,000 mediocre ones. Clean your data carefully: remove duplicates, ensure consistent formatting, and verify that every example demonstrates the behaviour you want.

When to fine-tune vs. prompt engineer: start with prompting. If you have tried few-shot prompting, system messages, and structured output and still cannot get consistent results, fine-tuning is the next step. Common fine-tuning use cases include: consistent output formatting, domain-specific classification, tone/style matching, and reducing prompt length (bake instructions into the model).

This module covers data preparation only — actual fine-tuning is too expensive and slow for a workshop setting. The concepts and data prep skills transfer directly to fine-tuning with OpenAI's API or open-source frameworks.

### Code Pattern

```python
import json

def prepare_fine_tuning_data(
    examples: list[dict],
    system_prompt: str,
) -> list[dict]:
    formatted = []
    for ex in examples:
        entry = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ex["input"]},
                {"role": "assistant", "content": ex["output"]},
            ]
        }
        formatted.append(entry)
    return formatted

def write_jsonl(data: list[dict], path: str) -> None:
    with open(path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")

def validate_jsonl(path: str) -> dict:
    errors = []
    with open(path) as f:
        for i, line in enumerate(f):
            try:
                entry = json.loads(line)
                if "messages" not in entry:
                    errors.append(f"Line {i}: missing 'messages'")
            except json.JSONDecodeError:
                errors.append(f"Line {i}: invalid JSON")
    return {"valid": len(errors) == 0, "errors": errors}
```

### When to Use

- When prompt engineering plateaus and you need consistent, domain-specific behaviour.
- Output format consistency, domain jargon, classification tasks.
- Trade-off: requires labelled data, training time, ongoing model management.

---

## 10. Advanced Guardrails

### Concept

Production LLM systems need multiple layers of protection. Content filtering catches toxic, harmful, or off-topic inputs and outputs. PII detection finds and redacts personal information (names, emails, phone numbers, SSNs) before they reach the model or appear in outputs. Schema validation ensures structured outputs conform to the expected format.

A guardrail pipeline chains these checks sequentially. For input: content filter → PII redactor → (pass to LLM). For output: (LLM response) → content filter → PII redactor → schema validator → (return to user). Each stage either passes the text through, modifies it (redaction), or rejects it entirely (content filter).

Content filtering can be rule-based (keyword lists, regex patterns) or LLM-based (ask the model to classify the text). LLM-based filters are more flexible but add latency. PII detection typically uses regex patterns for structured PII (emails, phone numbers, SSNs) and NER models for unstructured PII (names, addresses). Schema validation with Pydantic ensures that structured outputs have the right fields, types, and constraints.

The key design principle is defence in depth: no single guardrail is perfect, so layer multiple checks. A toxic prompt might slip past a keyword filter but get caught by an LLM classifier. A PII-containing response might miss the regex but get caught by a secondary NER check. Each layer reduces the probability of a harmful interaction.

### Code Pattern

```python
import re
from pydantic import BaseModel, ValidationError

def check_content(text: str, blocked_patterns: list[str]) -> dict:
    for pattern in blocked_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {"passed": False, "reason": f"Matched blocked pattern: {pattern}"}
    return {"passed": True, "reason": None}

def redact_pii(text: str) -> str:
    patterns = {
        "email": r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    }
    for pii_type, pattern in patterns.items():
        text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
    return text

class SafeResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str]

def validate_output(data: dict) -> dict:
    try:
        validated = SafeResponse(**data)
        return {"valid": True, "data": validated.model_dump()}
    except ValidationError as e:
        return {"valid": False, "errors": str(e)}
```

### When to Use

- Every production system handling user input.
- Regulated industries (healthcare, finance, legal) with strict data handling requirements.
- Trade-off: each guardrail adds latency; overly strict filters reduce usefulness.

---

## 11. Semantic Caching

### Concept

Traditional caching uses exact key matching — the same query string returns the same cached response. But users rarely ask the exact same question twice. "What is the capital of France?" and "What's France's capital city?" are semantically identical but have different cache keys. Semantic caching uses embedding similarity instead of exact matching.

The workflow is: (1) embed the incoming query, (2) search the cache for entries with similar embeddings, (3) if the most similar entry exceeds a similarity threshold (e.g., 0.95), return the cached response, (4) otherwise, process the query normally and cache the result with its embedding.

The similarity threshold is critical. Too low (0.8) and you return cached answers for genuinely different questions. Too high (0.99) and the cache rarely hits. Start with 0.95 and adjust based on your domain. Narrow domains (company FAQ) can use lower thresholds; broad domains (general knowledge) need higher thresholds.

Implementation-wise, the cache is just a vector store with metadata. Each entry stores the query embedding, the original query text, the response, and a timestamp. You can use the same vector database you use for document retrieval, or a dedicated lightweight store. Add TTL (time-to-live) to cache entries so stale information expires automatically.

Semantic caching dramatically reduces costs and latency for systems with repetitive query patterns (customer support, FAQ, internal tools). A well-tuned cache can serve 30-60% of queries from cache, cutting LLM costs proportionally.

### Code Pattern

```python
import numpy as np
from openai import OpenAI

class SemanticCache:
    def __init__(self, client: OpenAI, threshold: float = 0.95):
        self.client = client
        self.threshold = threshold
        self.entries: list[dict] = []

    def _embed(self, text: str) -> list[float]:
        resp = self.client.embeddings.create(
            model="text-embedding-3-small", input=text,
        )
        return resp.data[0].embedding

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def get(self, query: str) -> str | None:
        query_emb = self._embed(query)
        for entry in self.entries:
            sim = self._cosine_similarity(query_emb, entry["embedding"])
            if sim >= self.threshold:
                return entry["response"]
        return None

    def set(self, query: str, response: str) -> None:
        self.entries.append({
            "query": query,
            "embedding": self._embed(query),
            "response": response,
        })
```

### When to Use

- High-traffic systems with repetitive queries (customer support, FAQ bots).
- When LLM costs are a concern and many queries are paraphrases.
- Trade-off: threshold tuning is tricky; stale cache entries can return outdated information.

---

## 12. Multimodal RAG

### Concept

Standard RAG handles text, but real-world knowledge bases contain images, diagrams, charts, and photos. A maintenance manual includes wiring diagrams. A medical record includes X-rays. A product catalog includes photos. Multimodal RAG extends the retrieval pipeline to handle these non-text modalities.

The approach depends on your embedding model. If you have a multimodal embedding model (like CLIP), you can embed images directly alongside text and search across modalities. More commonly, you use a vision model to generate text descriptions of images, then embed those descriptions and store them in your text vector store. This "describe-then-embed" approach works with any text embedding model.

The indexing pipeline becomes: (1) for text documents, chunk and embed as usual, (2) for images, use a vision model to generate a detailed description, then embed the description, (3) store both in the same vector store with metadata indicating the source type and a reference to the original image. At query time, the search returns both text chunks and image descriptions, and the generation step can reference both.

For generation, you can either include image descriptions in the text context (simpler) or use a vision-capable model and pass the actual images alongside text (richer but more expensive). The choice depends on whether the image details in the description are sufficient or whether the model needs to see the actual image.

### Code Pattern

```python
from openai import OpenAI
import base64

def describe_image(client: OpenAI, image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in detail for indexing."},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{image_data}",
                }},
            ],
        }],
    )
    return response.choices[0].message.content

def index_multimodal(client, items: list[dict], collection):
    for item in items:
        if item["type"] == "text":
            text = item["content"]
        elif item["type"] == "image":
            text = describe_image(client, item["path"])
        embedding = client.embeddings.create(
            model="text-embedding-3-small", input=text,
        )
        collection.add(
            ids=[item["id"]],
            embeddings=[embedding.data[0].embedding],
            documents=[text],
            metadatas=[{"type": item["type"], "source": item.get("path", "")}],
        )
```

### When to Use

- Knowledge bases with diagrams, photos, charts, or screenshots.
- Product catalogs, medical records, technical manuals.
- Trade-off: vision model calls are expensive; descriptions may miss visual details.

---

## 13. Contextual Chunking

### Concept

How you chunk documents has a massive impact on retrieval quality. Naive fixed-size chunking (500 tokens per chunk) splits text at arbitrary boundaries, often breaking sentences, separating a topic across chunks, or burying key information in a chunk full of irrelevant context. Better chunking strategies are context-aware.

**Parent-child chunking** uses small chunks for search precision but retrieves the parent (larger chunk) for generation context. You index 100-token child chunks for fine-grained matching, but when a child matches, you return its parent (500-token chunk) to the LLM. This gives you the best of both worlds: precise retrieval and rich context.

**Overlapping windows** add redundancy at chunk boundaries. If you split at position 500 with a 100-token overlap, chunk 1 covers tokens 0-500 and chunk 2 covers tokens 400-900. This ensures that information near a boundary appears in at least one chunk's core.

**Semantic chunking** splits at natural topic boundaries rather than fixed positions. You can detect boundaries by computing embeddings for each sentence and splitting where the similarity between consecutive sentences drops below a threshold. This keeps related information together and separates unrelated sections.

The choice depends on your content. Structured documents (legal contracts, technical specs) benefit from semantic chunking. Long narratives benefit from parent-child. Short documents may not need chunking at all. Experiment with your actual data — chunking strategy is one of the highest-leverage knobs in a RAG system.

### Code Pattern

```python
def parent_child_chunk(
    text: str,
    parent_size: int = 500,
    child_size: int = 100,
    overlap: int = 20,
) -> list[dict]:
    words = text.split()
    chunks = []
    parent_id = 0
    for parent_start in range(0, len(words), parent_size):
        parent_text = " ".join(words[parent_start:parent_start + parent_size])
        parent_words = words[parent_start:parent_start + parent_size]
        for child_start in range(0, len(parent_words), child_size - overlap):
            child_text = " ".join(parent_words[child_start:child_start + child_size])
            if child_text.strip():
                chunks.append({
                    "parent_id": parent_id,
                    "parent_text": parent_text,
                    "child_text": child_text,
                })
        parent_id += 1
    return chunks
```

### When to Use

- Any RAG system — chunking strategy is one of the highest-leverage improvements.
- Parent-child: when you need precise matching but rich context for generation.
- Semantic chunking: when documents cover multiple topics.
- Trade-off: more sophisticated chunking requires more indexing logic and storage.

---

## Exercises

| # | Topic | Directory |
|---|-------|-----------|
| 01 | Hybrid Search | `exercises/01-hybrid-search/` |
| 02 | Re-ranking | `exercises/02-reranking/` |
| 03 | HyDE | `exercises/03-hyde/` |
| 04 | Agentic RAG | `exercises/04-agentic-rag/` |
| 05 | Citation Verification | `exercises/05-citation-verification/` |
| 06 | Web Search Backend | `exercises/06-web-search-backend/` |
| 07 | Text-to-SQL | `exercises/07-text-to-sql/` |
| 08 | LLM Eval | `exercises/08-llm-eval/` |
| 09 | Fine-tuning Data Prep | `exercises/09-fine-tuning-data/` |
| 10 | Guardrails | `exercises/10-guardrails/` |
| 11 | Semantic Caching | `exercises/11-semantic-cache/` |
| 12 | Multimodal RAG | `exercises/12-multimodal-rag/` |
| 13 | Contextual Chunking | `exercises/13-contextual-chunking/` |

## Running Tests

```bash
pytest module-11-edge-topics/
```

## Slides

```bash
pnpm slides:11
# or
cd module-11-edge-topics/slides && pnpm dev
```
