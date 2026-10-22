# Module 1 — Working with the LLM

> Time to talk to the model. After building a solid Python foundation, this module is your "hello world" with LLMs — making real API calls, building a CLI chat interface where users type questions and see answers stream back token by token, and learning how to craft prompts that get the results you want. By the end of this module you have a working chatbot and a toolkit of prompting techniques you can apply immediately.

## Learning goals

- Call the LLM directly with OpenAI's **Responses API** (instructions, input, message roles, the response object).
- Recognise the older **Chat Completions API** — still supported and common in existing code, but being phased out.
- Build a **CLI chat loop** with conversation history.
- **Stream responses** token by token for real-time output.
- Apply **prompting patterns** that hold up in production (personas, format constraints, guardrails, few-shot examples).

---

## The chat loop

The core pattern is a function that calls OpenAI's **Responses API**:

```python
import os
from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

def chat(client, messages):
    response = client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages)
    return response.output_text
```

`input` takes either a plain string or a list of messages (`{"role": "system" | "user" | "assistant", "content": ...}`). `response.output_text` is the model's reply as a string. For a single question you can also put the system prompt in `instructions` and the question straight into `input`:

```python
response = client.responses.create(
    model=MODEL,
    reasoning={"effort": "none"},
    instructions="You are the DSS Pathfinder ship AI.",
    input="What is our heading?",
)
```

Every script in this course reads the model name from `OPENAI_MODEL` (set it in `.env`) and falls back to `gpt-6-luna`, a fast, cheap model. `gpt-6-luna` is a *reasoning* model: by default it thinks before it answers. `reasoning={"effort": "none"}` turns that off, so it answers straight away like a classic chat model — you will see it on every call in this course.

The model sees the full context you send every time — that is how it "remembers" the conversation. The catch is that the history grows with every turn. When it exceeds the model's context window you need to truncate or summarise (covered in Module 7).

Wrap this in an input loop:

```python
messages = [{"role": "system", "content": "You are the DSS Pathfinder ship AI."}]

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("quit", "exit"):
        break
    messages.append({"role": "user", "content": user_input})
    response = chat(client, messages)
    messages.append({"role": "assistant", "content": response})
    print(f"AI: {response}")
```

---

## Streaming responses

With streaming, the first token appears in ~200ms and words flow in as they are generated. The total time is the same, but perceived latency drops dramatically.

```python
def stream_response(client, messages):
    stream = client.responses.create(
        model=MODEL, reasoning={"effort": "none"}, input=messages, stream=True,
    )
    tokens = []
    for event in stream:
        if event.type == "response.output_text.delta":
            sys.stdout.write(event.delta)
            sys.stdout.flush()
            tokens.append(event.delta)
    print()
    return "".join(tokens)
```

A stream is a sequence of typed **events**. Text arrives in `response.output_text.delta` events, each carrying a fragment in `event.delta`; other events (`response.created`, `response.completed`, ...) mark progress. Print each fragment immediately and the user sees words appear as they are generated. Progressive rendering keeps the user engaged during generation.

---

## Two APIs: Responses and Chat Completions

OpenAI has two APIs for generating text. This course uses the **Responses API**. You will still meet the older **Chat Completions API** — in existing code, tutorials, and the "OpenAI-compatible" endpoints many other providers offer — so it is worth recognising:

```python
# Chat Completions (older)
completion = client.chat.completions.create(
    model=MODEL,
    reasoning_effort="none",
    messages=[
        {"role": "system", "content": "You are the DSS Pathfinder ship AI."},
        {"role": "user", "content": "What is our heading?"},
    ],
)
text = completion.choices[0].message.content
```

| | Responses API (use this) | Chat Completions (older) |
|-|--------------------------|--------------------------|
| Call | `client.responses.create(...)` | `client.chat.completions.create(...)` |
| Input | `input=` (string or messages) + optional `instructions=` | `messages=` only |
| Reply text | `response.output_text` | `completion.choices[0].message.content` |
| Reasoning | `reasoning={"effort": "none"}` | `reasoning_effort="none"` |
| Streaming | typed events (`response.output_text.delta`) | chunks (`chunk.choices[0].delta.content`) |
| Conversation state | you send the history, **or** pass `previous_response_id` and the API keeps it | you always send the full history |
| Built-in tools | web search, file search, code interpreter, ... | not available |

Chat Completions is still supported, but OpenAI builds new features for the Responses API first and recommends it for new projects — existing apps are being migrated across. If you need to port old code, see the [migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses).

**Server-side conversation state.** Instead of resending the whole history, you can chain calls:

```python
first = client.responses.create(model=MODEL, input="My call sign is Nova-7.")
reply = client.responses.create(model=MODEL, previous_response_id=first.id, input="What is my call sign?")
```

The exercises keep the explicit message list, because seeing exactly what the model receives is the point of this module — and it is the pattern later modules build on for memory and agents.

---

## Prompt engineering

Everything the model does starts with the **system prompt**. A good prompt tells the model who it is, how it should respond, and what it should refuse.

**Persona** prompts give the model a character:

```python
"You are a pirate captain. Speak in exaggerated pirate slang. Never break character."
```

**Format constraints** control output shape:

```python
"Always respond in bullet points starting with '- '. No introductory or closing text."
```

**Guardrails** restrict scope:

```python
"You ONLY answer questions about astronomy. For anything else, say: 'I can only help with astronomy.'"
```

**Few-shot examples** teach patterns by showing input/output pairs directly in the prompt:

```python
"""Classify ship events. Examples:

User: The engine overheated.
Assistant: ENGINEERING: Engine temperature exceeded safe limits.

Follow this format exactly: CATEGORY: one-line explanation."""
```

The key insight is that prompts are **instructions, not wishes**. Vague prompts get vague results. Specific, explicit prompts with clear rules and examples get consistent output.

---

## Field rules

- **Stream by default.** Waiting 5 seconds for a response feels broken.
- **Prompt with intent.** Vague instructions get vague results. Be explicit about format, scope, and persona.

---

## Demo

One script walks through the whole module — basic chat, streaming, prompting patterns, and the Responses vs Chat Completions comparison:

```bash
python module-01-working-with-the-llm/demo/demo.py
```

## Exercises

The exercises chain — each one builds on the previous. Run them with `python start.py` for an interactive chat, or use `pytest` to validate.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-first-chat`](exercises/01-first-chat/) | Make your first LLM API call and build an input loop. |
| [`exercises/02-streaming`](exercises/02-streaming/) | Upgrade the chat to stream responses token by token. |
| [`exercises/03-prompting`](exercises/03-prompting/) | Write system prompts that control persona, format, guardrails, and few-shot patterns. |

Run tests for this module:

```bash
pytest module-01-working-with-the-llm/
```

## Slides

From repo root: `pnpm slides:01`, or `cd module-01-working-with-the-llm/slides && pnpm dev`.

## Reference

- [OpenAI — Text generation with the Responses API](https://developers.openai.com/api/docs/guides/text)
- [OpenAI — Streaming responses](https://developers.openai.com/api/docs/guides/streaming-responses)
- [OpenAI — Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
- [OpenAI — Migrating from Chat Completions to Responses](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [OpenAI — Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
