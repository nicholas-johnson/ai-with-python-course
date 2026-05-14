# Module 4 — GenAI Strategies

> Build a real AI application. This module closes Day 1 by combining everything from Modules 1–3 into a **Research Assistant** -- a web app where you chat with an AI that fetches web pages, saves notes, analyses images, and transcribes audio. A Svelte frontend is provided; features light up as you implement each backend endpoint.

## Learning goals

- Build a **FastAPI app** with SSE streaming chat, tool integration, and multimodal endpoints.
- Apply **prompt engineering**: system prompts, structured outputs, and grounding.
- Work with **multimodal** inputs: vision/image analysis via GPT-4o, speech-to-text via Whisper.
- Connect an **MCP server** to a web API for real-time tool use.
- Reason about **model selection** trade-offs: quality, cost, latency.
- Count tokens and enforce **budgets** before calling the model.
- Apply **guardrails**: schema validation, content filters, and confidence thresholds.

---

## The project

Delegates build the backend for an **AI Research Assistant** across three chained exercises. A Svelte + ShadCN + Tailwind frontend is provided in `frontend/`. Each exercise adds a new capability -- the frontend progressively lights up as endpoints come online.

```
frontend/          <- Provided. pnpm dev to start.
exercises/
  01-chat-api/     <- Streaming chat API
  02-tool-chat/    <- MCP server + tool-calling loop
  03-multimodal/   <- Vision + audio endpoints
```

---

## Prompt engineering principles

The difference between a flaky demo and a production AI is prompt engineering. A well-crafted prompt constrains the model's output so your code can reliably parse and act on it.

**Be specific.** Vague prompts produce vague answers. "Tell me about the topic" could return anything. "Return a JSON object with fields `title`, `summary`, and `key_points`" gives the model a target.

**System prompt** — the first message in the conversation. It sets persona, constraints, available tools, and output format. Think of it as the agent's standing orders.

**Few-shot examples** — include 2-3 example user/assistant pairs in the prompt to teach format, tone, and reasoning style in-context. Place them after the system prompt, before the real query.

```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    # Few-shot example
    {"role": "user", "content": "Summarise the Wikipedia article on transformers."},
    {"role": "assistant", "content": json.dumps({
        "title": "Transformer (deep learning)",
        "summary": "A neural network architecture based on self-attention.",
        "key_points": ["Introduced in 2017", "Replaced RNNs", "Powers GPT, BERT, etc."]
    })},
    # Real query
    {"role": "user", "content": actual_query},
]
```

Diminishing returns kick in after about 5 examples — keep them tight.

**Grounding** anchors answers to retrieved data, not the model's imagination. You will build full grounding pipelines in Modules 6 and 10.

---

## Structured outputs

Free-text responses are hard to parse. A structured output prompt constrains the model to return valid JSON matching a specific schema:

```python
SYSTEM = """You are a research assistant.
Return ONLY valid JSON matching this schema:
{
  "title": "string",
  "summary": "one paragraph",
  "key_points": ["string", ...]
}
Do not include any text outside the JSON object."""
```

On the receiving end, `json.loads` is the simplest validator. For production, use Pydantic `model_validate_json` which gives you type coercion, field constraints, and clear error messages when the model's output drifts.

---

## Model selection trade-offs

Not every query needs GPT-4o. Simple classification tasks run fine on GPT-4o-mini at 10-50x lower cost. The rule of thumb: **start with the cheapest model that passes your eval suite**, then upgrade only where quality demands it.

| Dimension | Premium (GPT-4o) | Budget (GPT-4o-mini) |
| --------- | ---------------- | -------------------- |
| Quality | Best reasoning | Good for classification |
| Cost | Higher per token | 10-50x cheaper |
| Latency | Slower | Faster |
| Context | 128k tokens | 128k tokens |

---

## Token counting and budgets

Every token costs money and counts against the context window. Before sending a request, count the tokens and trim if necessary. The `tiktoken` library gives you exact counts for OpenAI models.

```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")

def count_tokens(text: str) -> int:
    return len(enc.encode(text))

def enforce_budget(messages, max_tokens):
    """Drop oldest user turns until under budget."""
    total = sum(count_tokens(m["content"]) for m in messages)
    while total > max_tokens and len(messages) > 2:
        removed = messages.pop(1)  # keep system prompt at index 0
        total -= count_tokens(removed["content"])
    return messages
```

Always preserve the system prompt — it sets the agent's behaviour. Trim from the oldest turns first, since recent context is more relevant.

---

## Multimodal inputs

Modern models can process images and audio alongside text.

**Vision** — send images as base64 data URIs or public URLs in the message content:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe what you see."},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{img_b64}"
            }},
        ],
    }],
)
```

Content is a list of parts — text and images mixed freely. This works with base64 data URIs or public HTTPS URLs.

**Audio** — the Whisper API transcribes speech to text. Send raw audio bytes to the transcription endpoint and get back a transcript you can feed into the chat pipeline.

---

## Guardrails — defence in depth

A single check is not enough. Chain multiple guardrails, fail early, and log every decision.

**Schema validation** — does the model's response parse into the expected Pydantic model? If not, retry or fall back.

**Content filter** — scan for blocked terms (toxic content, off-topic responses, known hallucination patterns).

**Confidence threshold** — if the model's self-reported confidence is below a threshold, return "I'm not sure" instead of a potentially wrong answer.

```python
def run_guardrails(response, schema, blocked_terms, min_confidence):
    try:
        data = schema.model_validate_json(response)
    except ValidationError as e:
        return GuardrailResult(passed=False, reason=f"Schema: {e}")

    for term in blocked_terms:
        if term.lower() in response.lower():
            return GuardrailResult(passed=False, reason=f"Blocked: {term}")

    if data.confidence < min_confidence:
        return GuardrailResult(passed=False, reason="Low confidence")

    return GuardrailResult(passed=True, data=data)
```

---

## Field rules

- **Constrain the output format.** JSON schema in the system prompt beats hoping for structure.
- **Count tokens before you send.** Surprise truncation is worse than deliberate trimming.
- **Chain guardrails, never skip them.** Schema → filter → confidence. Fail fast, log always.

---

## Demos

```bash
python module-04-genai-strategies/demo/demo.py
```

Walks through all three topics interactively — press Enter between sections:
1. **Prompt engineering** — vague vs specific prompts, `response_format=json_object`, few-shot classification
2. **Model selection** — same task on GPT-4o vs GPT-4o-mini, comparing latency, tokens, and quality
3. **Guardrails** — Pydantic schema validation, content filtering, confidence gating — 4 test cases then a live LLM response

## Exercises

| # | Folder | What you build |
|---|--------|---------------|
| 1 | [`exercises/01-chat-api`](exercises/01-chat-api/) | **Streaming Chat** — FastAPI with SSE streaming `/chat` and `/health` endpoints. |
| 2 | [`exercises/02-tool-chat`](exercises/02-tool-chat/) | **MCP Research Tools** — Build an MCP server with web fetch + notes, extend chat with a tool-calling loop. |
| 3 | [`exercises/03-multimodal`](exercises/03-multimodal/) | **Vision & Audio** — Add `/vision` (GPT-4o image analysis) and `/transcribe` (Whisper) endpoints. |

### Frontend

The Svelte frontend lives in `frontend/`. Start it with:

```bash
cd module-04-genai-strategies/frontend
pnpm install
pnpm dev
```

It connects to `http://localhost:8000` (via Vite proxy). Features light up as you implement each backend endpoint.

### Run tests

```bash
pytest module-04-genai-strategies/
```

## Slides

From repo root: `pnpm slides:04`, or `cd module-04-genai-strategies/slides && pnpm dev`.

## Reference

- [OpenAI — Prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [OpenAI — Vision](https://platform.openai.com/docs/guides/vision)
- [OpenAI — Speech to text](https://platform.openai.com/docs/guides/speech-to-text)
- [FastAPI — Server-Sent Events](https://fastapi.tiangolo.com/)
- [sse-starlette](https://github.com/sysid/sse-starlette)
- [tiktoken (OpenAI tokenizer)](https://github.com/openai/tiktoken)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
