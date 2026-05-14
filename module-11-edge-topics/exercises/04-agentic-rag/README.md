# Exercise 04 — Agentic RAG

## Recap

In standard RAG, retrieval is a fixed pipeline step. In **agentic RAG**, the LLM decides whether to retrieve at all, what to search for, and when to stop. Retrieval is a tool the agent calls on demand, enabling multi-hop reasoning and skipping unnecessary searches.

## Your Task

1. Define `SEARCH_TOOL` — an OpenAI function-calling tool definition for document search.
2. Implement `handle_tool_call(tool_call, search_fn)` — execute a tool call and return results.
3. Implement `agentic_rag(client, question, search_fn, max_turns)` — the agent loop.

## Steps

1. Open `start.py` and review the tool definition structure.
2. Define the search tool with a `query` parameter.
3. Implement `handle_tool_call`: parse arguments, call search_fn, return results.
4. Implement the agent loop: send messages → check for tool calls → handle them → repeat until done.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/04-agentic-rag/test_start.py -v
```

## Stretch Goals

- Add a second tool (e.g., `get_document_by_id`) for the agent to fetch full documents.
- Add a `max_turns` parameter to prevent infinite loops.
- Log each tool call to see the agent's reasoning process.
