# Module 1 — Working with the LLM

> Time to talk to the model. After building a solid Python foundation, this module is your "hello world" with LLMs — making real API calls, building a CLI chat interface where users type questions and see answers stream back token by token, and learning how to craft prompts that get the results you want. By the end of this module you have a working chatbot and a toolkit of prompting techniques you can apply immediately.

## Learning goals

- Call the **LLM chat-completion API** directly (message roles, parameters, responses).
- Build a **CLI chat loop** with conversation history.
- **Stream responses** token by token for real-time output.
- Apply **prompting patterns** that hold up in production (personas, format constraints, guardrails, few-shot examples).

---

## The chat loop

The core pattern is a function that calls the OpenAI API:

```python
from openai import OpenAI

client = OpenAI()

def chat(client, messages):
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content
```

The model sees the full context every time — that is how it "remembers" the conversation. The catch is that the history grows with every turn. When it exceeds the model's context window you need to truncate or summarise (covered in Module 7).

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
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, stream=True,
    )
    tokens = []
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            sys.stdout.write(content)
            sys.stdout.flush()
            tokens.append(content)
    print()
    return "".join(tokens)
```

Each chunk contains a `delta` with a fragment of the response. Print it immediately and the user sees words appear as they are generated. Progressive rendering keeps the user engaged during generation.

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

One script walks through the whole module — basic chat, streaming, and prompting patterns:

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

- [OpenAI API — Chat completions](https://platform.openai.com/docs/guides/text-generation)
- [OpenAI — Prompt engineering](https://platform.openai.com/docs/guides/prompt-engineering)
