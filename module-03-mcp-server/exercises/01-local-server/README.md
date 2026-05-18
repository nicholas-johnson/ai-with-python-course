# Exercise 01 — Local MCP Server: Power Grid

## Goal

Build a **stdio MCP server** for managing the station's power grid. The agent harness is provided — you just build the server.

## What you build

In `starter/server.py`, implement three tools:

### `get_power_status(module: str)`

Look up a module in `POWER_GRID` and return its power level, capacity, load, and status as JSON. Return an error if the module doesn't exist.

### `allocate_power(source: str, target: str, amount: int)`

Transfer power between two modules. Validate:
- Both modules exist
- Source has enough power (`power_level >= amount`)
- Target won't exceed capacity (`power_level + amount <= capacity`)

On success, update the grid and return a success JSON. On failure, return an error.

### `list_alerts()`

Return the `ALERTS` list as JSON.

## Data

The power grid data is already defined in `server.py`:

| Module   | Power | Capacity | Load | Status  |
|----------|-------|----------|------|---------|
| habitat  | 850   | 1000     | 720  | online  |
| lab      | 600   | 800      | 580  | online  |
| docking  | 300   | 500      | 150  | standby |
| comms    | 400   | 400      | 390  | warning |

## Run it

```bash
# Run tests
pytest test_start.py -v

# Chat with the agent
python starter/agent.py
```

## Try it

- "What's the power status of the comms module?"
- "Transfer 100 units from habitat to docking"
- "Are there any power alerts?"
- "Can we send more power to comms?"
