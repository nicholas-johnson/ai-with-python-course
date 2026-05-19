# Module 5 Demo — RAG with ChromaDB

This demo walks through a complete RAG pipeline: ingest documents, search them via an MCP server, and chat with an agent that uses the tools.

## Prerequisites

- `OPENAI_API_KEY` environment variable set

## Walkthrough

All commands run from this directory (`module-05-rag-fundamentals/demo/`).

### 1. Ingest ship logs

```bash
python ingest.py
```

This loads `data/ship_logs.json`, chunks the content, embeds with `text-embedding-3-small`, and stores everything in a local ChromaDB database (`chroma_data/`).

Options:
- `--chunk-size 300` -- try smaller chunks
- `--overlap 30` -- adjust overlap
- `--reset` -- wipe and rebuild the collection

### 2. (Optional) Inspect the MCP server

```bash
python -m mcp dev server.py
```

Opens the MCP Inspector in your browser. You can call each tool individually and see raw JSON responses. Try:
- `search_docs` with `query: "hull damage"`
- `list_sources` to see all document IDs
- `ask_docs` with `question: "What happened in sector 7?"`

### 3. Chat with the RAG agent

```bash
python agent.py
```

This spawns `server.py` as a subprocess, discovers its tools, and runs an interactive chat loop. The agent uses OpenAI tool calling to query the document index.

Commands:
- Type any question to chat
- `/tools` -- list available MCP tools
- `quit` -- exit

## Files

| File | Purpose |
|------|---------|
| `ingest.py` | Load, chunk, embed, store |
| `server.py` | FastMCP server with RAG tools |
| `agent.py` | MCP client + OpenAI agent loop |
