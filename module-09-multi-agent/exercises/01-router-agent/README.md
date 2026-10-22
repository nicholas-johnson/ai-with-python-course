# Exercise 01 — Router + Specialist Agents

## Recap

In a multi-agent system, a **router** is the front door. It classifies an incoming message and dispatches it to the right **specialist agent**. Each specialist has its own focused system prompt and domain expertise, which produces higher-quality answers than a single generalist prompt.

The classification step can be simple keyword matching, but using an LLM is more robust -- it handles ambiguous queries and understands intent. With **structured outputs**, a `Literal` type means the model can only answer with a valid department:

```python
class Route(BaseModel):
    department: Literal["medical", "tactical", "comms"]

def classify_query(query: str, client: OpenAI) -> str:
    response = client.responses.parse(
        model=MODEL,
        reasoning={"effort": "none"},
        text_format=Route,
        input=[
            {"role": "system", "content": "Classify the query into a department."},
            {"role": "user", "content": query},
        ],
    )
    route = response.output_parsed
    return route.department if route else "medical"
```

Each specialist agent is a simple function: it takes a query, runs it through the LLM with a domain-specific system prompt, and returns the response.

## What you build

A console app in **`start.py`** with three specialist agents (medical, tactical, comms) and an LLM-powered router. The system prompt for each specialist is already provided -- you implement the functions that use them.

**Key functions:**

| Function | Description |
|---|---|
| `classify_query` | Structured-output LLM call that classifies a query into a department |
| `specialist_agent` | Runs a specialist with the right system prompt |
| `route_and_respond` | Pipeline: classify then dispatch, returning both the routing decision and response |

## Step-by-step

### 1. Implement `classify_query`

Use `client.responses.parse` to classify a query:

- Define `Route(BaseModel)` with `department: Literal["medical", "tactical", "comms"]` and pass it as `text_format`
- System prompt: describe what each department handles (you don't need to describe the JSON -- the schema does)
- Return `response.output_parsed.department`
- If `response.output_parsed` is `None` (the model refused), default to `"medical"`

You no longer need to check for an invalid department name: the `Literal` constrains the model's output, and Pydantic would reject anything else.

### 2. Implement `specialist_agent`

Look up the system prompt from `SPECIALIST_PROMPTS` for the given department, then make a `client.responses.create` call:

- Use `SPECIALIST_PROMPTS.get(department, SPECIALIST_PROMPTS["medical"])` to handle unknown departments gracefully
- Pass the system prompt and the user query as messages
- Return the response text

### 3. Implement `route_and_respond`

Wire the two functions together:

1. Call `classify_query` to determine the department
2. Call `specialist_agent` with the department and query
3. Return `{"department": department, "response": response}`

### 4. Run the interactive loop

The `main()` function and command handling are already provided. Once you implement the core functions, these commands will work:

| Command | Action |
|---|---|
| any text | Route to a specialist and show the response |
| `/route <msg>` | Show which specialist would handle the message (without executing) |
| `/specialists` | List all available specialist agents |
| `quit` | Exit |

## Try it

```bash
cd module-09-multi-agent/exercises/01-router-agent
python start.py
```

Try different types of queries:
- "Crew radiation exposure levels?" (should route to medical)
- "Raise shields, hostiles incoming!" (should route to tactical)
- "Decrypt the incoming transmission" (should route to comms)

Use `/route` to check classification without executing the specialist.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `classify_query` returns a valid department name
- `classify_query` defaults to "medical" on bad JSON or unknown departments
- `specialist_agent` returns a non-empty string and uses the correct system prompt
- `route_and_respond` returns a dict with both keys and makes at least 2 LLM calls
- No real OpenAI calls -- all tests use mocked clients

## Stretch goals

- Add a fourth specialist (e.g. medical, security, or communications)
- Add confidence scoring: have the router return a confidence level and fall back to a general agent below a threshold
- Implement keyword-based routing as a fallback when the LLM is unavailable
