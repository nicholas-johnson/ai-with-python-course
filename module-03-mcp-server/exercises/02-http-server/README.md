# Exercise 02 — HTTP MCP Server: Science Lab

## Goal

Build an **HTTP MCP server** for the station's science lab. This server runs at a URL instead of as a subprocess — the same protocol, different transport.

## What you build

In `starter/server.py`, implement three tools:

### `list_experiments(status: str | None = None)`

Return all experiments as JSON. If `status` is provided (`"running"`, `"complete"`, or `"pending"`), filter to only matching experiments.

### `get_sample(sample_id: str)`

Look up a sample in `SAMPLES` by ID. Return its details as JSON (include the `sample_id`). Return an error if not found.

### `run_analysis(sample_id: str, method: str)`

Run an analysis method on a sample. Validate both the sample and method exist. Return JSON with the sample ID, method name, method description, and a result string. Return an error if either is invalid.

## Data

Already defined in `server.py`:

**Experiments**: 4 experiments with ID, title, status, and lead researcher.

**Samples**: S-101 (mineral), S-102 (biological), S-103 (gas), S-104 (mineral).

**Methods**: spectral, microscopy, mass_spec, culture.

## What's new

- `FastMCP("...", stateless_http=True)` — enables HTTP transport
- `server.run(transport="streamable-http")` — starts at `http://localhost:8000/mcp`
- The agent connects via `streamablehttp_client` instead of `stdio_client`

## Run it

```bash
# Run tests (these test the server directly, no HTTP needed)
pytest test_start.py -v

# Start the HTTP server
python starter/server.py

# In another terminal, run the agent (connects to both servers)
python starter/agent.py
```

## Try it

- "What experiments are currently running?"
- "Tell me about sample S-102"
- "Run spectral analysis on the asteroid belt mineral"
- "What's the power status of the lab?" (uses the power grid server from Ex01)
