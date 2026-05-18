# Exercise 2: RAG Chat

## Recap

A RAG (Retrieval-Augmented Generation) pipeline has three stages:

1. **Retrieve** -- find the most relevant chunks for the user's question
2. **Ground** -- build a prompt that includes those chunks as context, with source labels
3. **Generate** -- ask the LLM to answer using *only* the provided sources, citing them

The grounded prompt looks like this:

```
Answer the question using ONLY the sources below. Cite sources using [Source N].
If the sources don't contain the answer, say so.

[Source 1: LOG-015] Hull breach detected in sector 7...
[Source 2: LOG-015] Emergency repair teams dispatched...

Question: What happened in sector 7?
```

This forces the LLM to stay grounded in your data and makes hallucinations easy to spot -- if a claim doesn't have a `[Source N]` tag, it's probably made up.

## What you build

A console chat agent in **`start.py`** that uses the index from Exercise 1 to answer questions with citations. The Exercise 1 code (load, chunk, embed, search) is already inlined at the top of `start.py` — you'll add the grounded prompt and RAG chat below it.

**Key functions:**

| Function | Description |
|---|---|
| `build_grounded_prompt(query, passages)` | Construct the system + user prompt with `[Source N]` labels |
| `rag_chat(query, collection, k)` | Retrieve → ground → generate |

## Step-by-step

### 1. Review the inlined index builder

The Exercise 1 solution (`load_logs`, `chunk_text`, `build_index`, `search`) is already at the top of `start.py`. You don't need to change it — just call `build_index()` and `search()` in your code below.

### 2. Implement `build_grounded_prompt`

Takes the user's question and a list of retrieved passages. Returns a list of messages:

```python
def build_grounded_prompt(query: str, passages: list[dict]) -> list[dict]:
    context_parts = []
    for i, p in enumerate(passages, 1):
        source = p["metadata"].get("source_id", "unknown")
        context_parts.append(f"[Source {i}: {source}] {p['text']}")

    system = (
        "Answer the question using ONLY the sources below. "
        "Cite sources using [Source N]. "
        "If the sources don't contain the answer, say so."
    )
    context = "\n\n".join(context_parts)
    user_msg = f"{context}\n\nQuestion: {query}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]
```

### 3. Implement `rag_chat`

1. Call `search(collection, query, k)` to get passages
2. Call `build_grounded_prompt(query, passages)` to get the messages
3. Call OpenAI `chat.completions.create(model="gpt-4o-mini", messages=...)`
4. Return the answer and the passages used

### 4. Build the interactive loop

Handle these commands:

| Command | Action |
|---|---|
| any text | RAG chat -- retrieve, ground, generate |
| `/sources` | Show full text of the last retrieved passages |
| `/norag` | Re-ask the last question without retrieval |
| `/k <number>` | Change how many chunks are retrieved |
| `/prompt` | Show the full grounded prompt |
| `quit` | Exit |

## Try it

```bash
cd module-05-rag-fundamentals/exercises/02-rag-chat
python start.py
```

Ask questions about the scout logs: alien signals, first contact protocol, crew activities, xenolinguistics. Use `/norag` to compare RAG vs raw LLM answers.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `build_grounded_prompt` produces correctly structured messages with source labels
- `rag_chat` returns an answer string and source list

## Stretch goals

- Add streaming so the answer appears token by token
- Implement a confidence score based on how relevant the retrieved chunks are
- Try different values of `k` and observe how answer quality changes
