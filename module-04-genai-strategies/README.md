# Module 4 — GenAI Strategies

> Build a real AI application. This module closes Day 1 by combining everything from Modules 1–3 into a **Research Assistant** -- a web app where you chat with an AI that fetches web pages, saves notes, analyses images, and transcribes audio. A Svelte frontend is provided; features light up as you implement each backend endpoint.

## Learning goals

- Build a **FastAPI app** with SSE streaming chat, tool integration, and multimodal endpoints.
- Connect an **MCP server** to a web API for real-time tool use.
- Reason about **model selection** trade-offs: quality, cost, latency.
- Count tokens and enforce **budgets** before calling the model.
- Work with **multimodal** inputs: vision/image analysis via GPT-4o, speech-to-text via Whisper.
- Apply **guardrails**: schema validation, content filters, and confidence thresholds.

---

## The project

Delegates build the backend for an **AI Research Assistant** across two chained exercises. A Svelte + ShadCN + Tailwind frontend is provided in `frontend/`. Each exercise adds a new capability -- the frontend progressively lights up as endpoints come online.

```
frontend/              <- Provided. pnpm dev to start.
exercises/
  01-research-chat/    <- Streaming chat with MCP tools (server provided)
  02-multimodal/       <- Vision + audio endpoints
```

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

- **Count tokens before you send.** Surprise truncation is worse than deliberate trimming.
- **Chain guardrails, never skip them.** Schema → filter → confidence. Fail fast, log always.

---

## Demos

```bash
python module-04-genai-strategies/demo/demo.py
```

A quick multimodal demo — press Enter between sections:
1. **Vision** — sends a sample image to GPT-4o and prints the structured analysis
2. **Audio** — sends a sample WAV to Whisper and prints the transcript

## Exercises

| # | Folder | What you build |
|---|--------|---------------|
| 1 | [`exercises/01-research-chat`](exercises/01-research-chat/) | **Research Chat** — Streaming chat with MCP tool calling (server provided). Wire up SSE streaming, tool discovery, and the tool-calling loop. |
| 2 | [`exercises/02-multimodal`](exercises/02-multimodal/) | **Vision & Audio** — Add `/vision` (GPT-4o image analysis) and `/transcribe` (Whisper) endpoints. |

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

- [OpenAI — Vision](https://platform.openai.com/docs/guides/vision)
- [OpenAI — Speech to text](https://platform.openai.com/docs/guides/speech-to-text)
- [FastAPI — Server-Sent Events](https://fastapi.tiangolo.com/)
- [sse-starlette](https://github.com/sysid/sse-starlette)
- [tiktoken (OpenAI tokenizer)](https://github.com/openai/tiktoken)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
