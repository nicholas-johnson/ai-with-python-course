# Exercise 04 — Swarm Agents with Scoped Tools

## Recap

Exercises 01–03 use a **central controller** (router or supervisor) to decide which agent runs next. The **swarm / handoff pattern** is different: agents pass control **peer-to-peer**. Each agent has its own system prompt and a **scoped tool set**. When a query needs another department, the agent calls `transfer_to_<department>` — a special tool that hands the conversation to a colleague.

There is no supervisor in the loop. The active agent decides whether to use a domain tool, hand off, or answer the user.

```
User query → Comms (decrypt_signal)
           → transfer_to_engineering
           → Engineering (check_reactor)
           → final answer
```

This matches patterns in OpenAI Swarm and many production agent frameworks: **handoff as a tool**, **least-privilege tool access** per role.

## What you build

A console app in **`start.py`** where three officers (comms, engineering, tactical) each have exclusive mock ship tools plus transfer tools. Implement the swarm loop that runs tool rounds and follows handoffs until a plain-text answer or `max_hops`.

**Provided:** [`tools.py`](tools.py) — mock functions, `AGENT_TOOLS`, `TOOL_FUNCTIONS`, `AGENT_PROMPTS`.

**Key functions:**

| Function | Description |
|---|---|
| `build_agent_messages` | System prompt + user query for a department |
| `run_agent_turn` | One `chat.completions.create` with that agent's `tools` |
| `handle_tool_calls` | Run tools, build `role: tool` messages, detect transfers |
| `swarm_loop` | Loop: turn → tools → handoff or final answer |

## Step-by-step

### 1. Implement `build_agent_messages`

Look up `AGENT_PROMPTS[department]` and return:

```python
[
    {"role": "system", "content": prompt},
    {"role": "user", "content": query},
]
```

### 2. Implement `run_agent_turn`

- Model: `gpt-4o-mini`
- Pass `messages` and `tools=AGENT_TOOLS[department]`
- `tool_choice="auto"`
- Return `response.choices[0].message` (the message object, not just text)

### 3. Implement `handle_tool_calls`

For each `tool_call` on the assistant message:

1. Parse `tc.function.arguments` as JSON
2. If name starts with `transfer_to_`, call `TOOL_FUNCTIONS[name]()`, parse JSON for `transfer_to`, set `transfer_target`
3. Else call `TOOL_FUNCTIONS[name](**args)` for domain tools
4. Append an **assistant** message (with `tool_calls`) then **tool** messages with `tool_call_id`

Return `(tool_messages, transfer_target)`.

### 4. Implement `swarm_loop`

1. Start at `start_dept` with `build_agent_messages`
2. For each hop up to `max_hops`:
   - `run_agent_turn`
   - If no `tool_calls`, return final `answer`, `chain`, `trace`
   - `handle_tool_calls`, extend `messages`
   - If `transfer_target` is a valid other department, switch agent, append handoff user message, `continue`
   - Otherwise same agent gets another turn (more tools)
3. If hops exhausted, return a max-hops message

Record `chain` (departments visited) and `trace` (hop events for debugging).

### 5. Run the REPL

`main()` is provided. Commands:

| Command | Action |
|---|---|
| any text | Run swarm from the configured start agent |
| `/start <dept>` | Set starting agent (`comms`, `engineering`, `tactical`) |
| `/trace` | Show trace from last query |
| `/hops N` | Set max hops (default 6) |
| `/agents` | List agents and their tools |
| `quit` | Exit |

## Try it

```bash
cd module-09-multi-agent/exercises/04-swarm-tools
python start.py
```

Example queries:

- `Decrypt signal X42 and check if the reactor can handle a +15% power boost` (comms → engineering)
- `Scan for threats and report shield status` (tactical only)
- `Scan frequencies and tell me if anything looks hostile` (comms → tactical)

Use `/trace` to see handoffs and tool results.

## Tests

```bash
pytest test_start.py -v
```

Tests use a mocked OpenAI client — no real API calls.

## Stretch goals

- Add token/call counting and print cost summary after each swarm run
- Implement parallel fan-out: two agents research sub-questions, then a merger agent synthesises
- Add a `/dry-run` mode that prints which tools would be called without calling the LLM
- Fail closed: if a tool name is unknown, return an error tool result instead of crashing
