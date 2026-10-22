# Exercise 01 -- First Chat

> Make your first LLM API call, then build an interactive console chat.

## Recap

OpenAI's **Responses API** takes your input -- here, a list of **messages** -- and returns a response. Each message has a **role** -- `system`, `user`, or `assistant` -- that tells the model who said it:

```python
messages = [
    {"role": "system", "content": "You are the DSS Pathfinder ship AI."},
    {"role": "user", "content": "How many crew on board?"},
]
```

The `system` message sets the AI's personality and constraints. You send it once at the start. Every time the user speaks you append a `user` message, call the API, then append the `assistant` response. The model sees the **full list** every call -- that is how it "remembers" the conversation.

The key API call looks like this:

```python
import os
from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
response = client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages)
text = response.output_text
```

`model` selects which model to use. `MODEL` reads `OPENAI_MODEL` from your environment and defaults to `gpt-6-luna`, which is fast and cheap for development. `gpt-6-luna` is a reasoning model, and `reasoning={"effort": "none"}` tells it to answer directly without thinking first. `input` takes your messages list, and `response.output_text` gives you the reply as a plain string.

> **You may also see `client.chat.completions.create(messages=...)`** with the reply in `response.choices[0].message.content`. That's the older Chat Completions API -- still supported, but OpenAI recommends the Responses API for new code. The module README compares the two.

This exercise uses the `openai` package, which is already installed via the project's `pyproject.toml`.

## What you build

- **`chat(client, messages)`** -- a function that makes one API call and returns the response text.
- **`main(client)`** -- an input loop that reads from the console, calls `chat()`, and prints the result. The messages list grows with each turn so the model has context.

## Step-by-step

### 1. Implement `chat(client, messages) -> str`

Call `client.responses.create()` with `model=MODEL` and the `messages` list as `input`. Return the reply text.

```python
response = client.responses.create(model=MODEL, reasoning={"effort": "none"}, input=messages)
return response.output_text
```

The tests check that `chat()` returns a non-empty string and that it passes the messages list to the API correctly.

### 2. Implement `main(client)`

Build the conversation loop:

1. Create a `messages` list starting with `{"role": "system", "content": SYSTEM_PROMPT}`.
2. Use `input("You: ")` to read user input.
3. If the user types `"quit"` or `"exit"`, break out of the loop.
4. Append the user message: `{"role": "user", "content": user_input}`.
5. Call `chat(client, messages)` to get the response.
6. Append the assistant message: `{"role": "assistant", "content": response}`.
7. Print the response with a prefix like `AI:` or `\nAI:`.

The messages list grows with every exchange. This is what gives the model conversational memory.

## Try it

```bash
python start.py
```

Try these interactions:

- `"Hello, who are you?"` -- should introduce itself as the Pathfinder AI.
- `"What did I just ask you?"` -- should recall the previous message (conversational memory working).
- `"quit"` -- exits cleanly.

## Tests

```bash
pytest module-01-working-with-the-llm/exercises/01-first-chat/test_start.py -v
```

## Stretch goals

1. Add a system prompt that gives the AI a more specific personality (e.g. terse military style, or overly enthusiastic).
2. Print a message count after each response so you can see the context growing.
