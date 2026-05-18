# Exercise 03 — Ship Documentation Server (MCP Resources)

## Goal

Build a **stdio MCP server** that serves ship documentation as **MCP resources** and provides search tools. This introduces the distinction between resources (read-only data) and tools (actions).

## What you build

In `starter/server.py`, implement two resources and three tools.

### Resources

Resources are read-only data the client can pull into context.

#### `docs://index`

Return a formatted list of all available documents with their URIs.

#### `docs://{filename}`

Return the full markdown content of a specific document. Register one resource per `.md` file in the `docs/` folder.

### Tools

#### `search_docs(query: str)`

Search all markdown files for a keyword (case-insensitive). Return a JSON list of matches, each with `filename` and `snippet` (the matching line).

#### `read_doc(filename: str)`

Read the full contents of a ship document by filename. Sanitise the filename (strip path separators), then read the `.md` file from `docs/`. Return an error if the file doesn't exist.

#### `list_docs()`

Return a JSON list of all documents with `filename` and `title` (extracted from the first `#` heading).

## Data

The `docs/` folder contains 5 markdown files:

| File | Contents |
|------|----------|
| `emergency-procedures.md` | Alert levels, evacuation routes, hull breach protocol |
| `navigation-manual.md` | Coordinates, course plotting, sensor calibration |
| `crew-handbook.md` | Chain of command, duty rosters, communication |
| `engineering-guide.md` | Power systems, warp drive, shields |
| `medical-protocols.md` | First aid, quarantine, medical bay equipment |

## What's new

- **`@server.resource(uri)`** — registers a read-only resource
- Resources vs tools: resources provide context, tools perform actions
- Reading files from disk and serving them via MCP
- The agent uses `session.list_resources()` and `session.read_resource()` to pull docs

## Run it

```bash
# Run tests
pytest test_start.py -v

# Start the HTTP server (for the science lab from Ex02)
python starter/http_server.py

# In another terminal, run the agent
python starter/agent.py
```

## Try it

- "What are the evacuation routes?"
- "Search the docs for quarantine procedures"
- "What documents are available?"
- "What's the warp drive cooldown time?"
- "Show me the power status and search for shield maintenance info"
