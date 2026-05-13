# Module 3 — GenAI Strategies

> The agent can talk, call tools, and remember conversations. Now it is time to make it smart. This module pulls together everything from Day 1 — the agent core, the LLM integration, and session management — and layers on prompt engineering that produces reliable outputs, multimodal capabilities so the Pathfinder can analyse hull damage photos and bridge audio logs, and a chain of guardrails that catches bad responses before they reach the crew.

## Learning goals

- Apply **prompt engineering**: system prompts, few-shot examples, structured outputs, and grounding.
- Work with **multimodal** inputs and outputs: vision/image analysis, speech-to-text, text-to-speech.
- Reason about **model selection** trade-offs: quality, cost, latency.
- Count tokens and enforce **budgets** before calling the model.
- Chain **guardrails**: schema validation, content filters, and confidence thresholds.

---

## Prompt engineering principles

The difference between a flaky demo and a production AI is prompt engineering. A well-crafted prompt constrains the model's output so your code can reliably parse and act on it.

**Be specific.** Vague prompts produce vague answers. "Tell me about the crew" could return anything. "Return a JSON object with fields `name`, `role`, and `status` for each crew member in the science department" gives the model a target.

**System prompt** — the first message in the conversation. It sets persona, constraints, available tools, and output format. Think of it as the agent's standing orders.

**Few-shot examples** — include 2-3 example user/assistant pairs in the prompt to teach format, tone, and reasoning style in-context. Place them after the system prompt, before the real query.

```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    # Few-shot example
    {"role": "user", "content": "Kepler Sweep lost contact at 14:30."},
    {"role": "assistant", "content": json.dumps({
        "mission_id": "KS-7",
        "status": "aborted",
        "risk_level": "critical",
        "summary": "Contact lost during Kepler Sweep."
    })},
    # Real query
    {"role": "user", "content": actual_report},
]
```

The assistant message IS the example output. The model mirrors the format with no extra instructions needed. Diminishing returns kick in after about 5 examples — keep them tight.

**Grounding** anchors answers to retrieved data, not the model's imagination. You will build full grounding pipelines in Modules 6 and 10.

---

## Structured outputs

Free-text responses are hard to parse. A structured output prompt constrains the model to return valid JSON matching a specific schema:

```python
SYSTEM = """You are a mission analyst for the DSS Pathfinder.
Return ONLY valid JSON matching this schema:
{
  "mission_id": "string",
  "status": "active | completed | aborted",
  "risk_level": "low | medium | high | critical",
  "summary": "one sentence"
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

The Pathfinder's hull cameras capture images and the bridge records audio. Modern models can process both alongside text.

**Vision** — send images as base64 data URIs or public URLs in the message content:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe any damage visible."},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{img_b64}"
            }},
        ],
    }],
)
```

Content is a list of parts — text and images mixed freely. This works with base64 data URIs or public HTTPS URLs.

**Audio** — the Whisper API transcribes speech to text. Send raw audio bytes to the transcription endpoint and get back a transcript you can feed into the chat pipeline. Text-to-speech goes the other direction — convert the agent's response to spoken audio for hands-free bridge ops.

---

## Guardrails — defence in depth

A single check is not enough. Chain multiple guardrails, fail early, and log every decision.

**Schema validation** — does the model's response parse into the expected Pydantic model? If not, retry or fall back.

**Content filter** — scan for blocked terms (toxic content, off-topic responses, known hallucination patterns).

**Confidence threshold** — if the model's self-reported confidence is below a threshold, return "I'm not sure" instead of a potentially wrong answer.

```python
def run_guardrails(response, schema, blocked_terms, min_confidence):
    # Step 1: Schema check
    try:
        data = schema.model_validate_json(response)
    except ValidationError as e:
        return GuardrailResult(passed=False, reason=f"Schema: {e}")

    # Step 2: Content filter
    for term in blocked_terms:
        if term.lower() in response.lower():
            return GuardrailResult(passed=False, reason=f"Blocked: {term}")

    # Step 3: Confidence gate
    if data.confidence < min_confidence:
        return GuardrailResult(passed=False, reason="Low confidence")

    return GuardrailResult(passed=True, data=data)
```

Each guardrail returns early on failure — no wasted work. The structured result lets the caller decide what to do next (retry, fall back, or escalate).

---

## Field rules

- **Constrain the output format.** JSON schema in the system prompt beats hoping for structure.
- **Count tokens before you send.** Surprise truncation is worse than deliberate trimming.
- **Chain guardrails, never skip them.** Schema → filter → confidence. Fail fast, log always.

---

## Demos

```bash
python module-03-genai-strategies/demo/01_prompting_patterns.py
python module-03-genai-strategies/demo/02_model_selection.py
python module-03-genai-strategies/demo/03_guardrails.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-structured-prompts`](exercises/01-structured-prompts/) | Build prompts that yield **JSON-parseable** outputs. |
| [`exercises/02-token-budget`](exercises/02-token-budget/) | **Count tokens** and enforce a max budget before calling the model. |
| [`exercises/03-guardrail-chain`](exercises/03-guardrail-chain/) | Chain **schema validation**, **content filter**, and **confidence** threshold. |
| [`exercises/04-multimodal-analysis`](exercises/04-multimodal-analysis/) | Prepare **vision** and **audio** payloads, parse structured damage reports. |

Run tests for this module:

```bash
pytest module-03-genai-strategies/
```

## Slides

From repo root: `pnpm slides:03`, or `cd module-03-genai-strategies/slides && pnpm dev`.

## Reference

- [OpenAI — Prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic — Prompting long context](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
- [tiktoken (OpenAI tokenizer)](https://github.com/openai/tiktoken)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
