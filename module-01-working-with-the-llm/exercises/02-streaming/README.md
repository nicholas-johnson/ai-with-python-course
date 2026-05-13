# Exercise 02 -- Streaming Chat

> Upgrade the chat to stream responses token by token -- words flow in real time instead of appearing all at once.

## Recap

Without streaming, the user stares at a blank screen for several seconds while the model generates the full response. With streaming, the first token appears in ~200ms and words flow in as they are generated. The total time is the same, but the perceived latency drops dramatically.

To enable streaming, pass `stream=True` to the API call:

```python
response = client.chat.completions.create(
    model="gpt-4o-mini", messages=messages, stream=True,
)
```

This changes the return type from a single response object to an **iterator of chunks**. Each chunk has the same structure as a normal response, but instead of `.message` it has a `.delta` containing just the new fragment:

```python
for chunk in response:
    token = chunk.choices[0].delta.content  # may be None
    if token:
        sys.stdout.write(token)
        sys.stdout.flush()
```

`delta.content` is `None` for the first and last chunks (which carry metadata, not text). Always check before printing. Use `sys.stdout.write()` + `sys.stdout.flush()` rather than `print()` so tokens appear without newlines between them.

This exercise builds on Exercise 01. The basic `chat()` function and the input loop are already provided -- you only need to implement `stream_response()`.

## What you build

- **`stream_response(client, messages) -> str`** -- call the API with streaming, print each token as it arrives, and return the complete assembled text.

The chat loop in `main()` is provided and already calls `stream_response()` instead of `chat()`.

## Step-by-step

### 1. Implement `stream_response(client, messages) -> str`

Follow these steps inside the function:

1. Call `client.chat.completions.create(model=MODEL, messages=messages, stream=True)`.
2. Create an empty list to collect tokens.
3. Iterate over the response chunks with a `for` loop.
4. For each chunk, extract `chunk.choices[0].delta.content`.
5. If the content is not `None`, print it immediately with `sys.stdout.write(content)` followed by `sys.stdout.flush()`.
6. Append the content to your tokens list.
7. After the loop, print a newline (`print()`).
8. Return the joined tokens: `"".join(tokens)`.

The key pattern:

```python
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

The tests check that `stream_response()` returns the full text as a single string, and that it correctly handles the streaming API.

## Try it

```bash
python start.py
```

Try these interactions:

- Ask a longer question like `"Explain how warp drives work in 3 paragraphs"` -- you should see words appearing one by one rather than the whole response appearing at once.
- Compare with Exercise 01 -- same question, but now the response starts immediately.
- `"quit"` -- exits cleanly.

## Tests

```bash
pytest module-01-working-with-the-llm/exercises/02-streaming/test_start.py -v
```

## Stretch goals

1. Add a character delay (e.g. `time.sleep(0.01)`) between tokens to create a typewriter effect.
2. Count the tokens as they arrive and print a `[42 tokens]` summary after each response.
