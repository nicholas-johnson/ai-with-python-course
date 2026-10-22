# Exercise 04 — Agentic RAG

## Recap

### Standard RAG vs Agentic RAG

In **standard RAG**, retrieval is a fixed step: every question triggers a search, the results get stuffed into the prompt, and the LLM answers. This works, but it's rigid — what if the question doesn't need retrieval ("What's 2+2?"), or needs *multiple* searches ("Compare the engineering report with the medical log")?

In **agentic RAG**, the LLM is in control. Retrieval is a **tool** the LLM can choose to call — or not. The loop looks like:

1. Send the user's question to the LLM (along with a tool definition).
2. The LLM either answers directly, **or** asks to call the search tool.
3. If it called a tool: execute the search, feed results back, go to step 2.
4. Repeat until the LLM gives a final text answer (no more tool calls).

This lets the agent do multi-hop reasoning: search for one thing, read the results, decide it needs more info, search again with a refined query, and only then answer.

### How tool calling works with OpenAI

You define available tools as JSON objects and pass them in the API call. The LLM responds with either a normal text message or a structured tool call request:

```python
response = client.responses.create(
    model=MODEL,
    reasoning={"effort": "none"},
    input=messages,
    tools=[SEARCH_TOOL],  # tell the model what tools exist
)
calls = [item for item in response.output if item.type == "function_call"]

if calls:
    # The model wants to call a tool — execute it and feed results back
    tool_call = calls[0]
    args = json.loads(tool_call.arguments)  # e.g. {"query": "reactor safety"}
else:
    # The model is done — response.output_text has the final answer
    print(response.output_text)
```

### The tool definition format

A tool definition tells the model what the tool does and what parameters it accepts:

```python
SEARCH_TOOL = {
    "type": "function",
    "name": "search_documents",
    "description": "Search the document database for relevant information.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant documents.",
            },
        },
        "required": ["query"],
    },
}
```

## What you build

Three pieces in **`start.py`** — a tool definition and two functions:

| Item | What it does |
|---|---|
| `SEARCH_TOOL` | JSON tool definition telling the model about the search function |
| `handle_tool_call(tool_call, search_fn)` | Parse the model's tool call and execute the search |
| `agentic_rag(client, question, search_fn, max_turns)` | The full agent loop |

## Data format

The `search_fn` you're given takes a query string and returns a list of result strings:

```python
def my_search(query: str) -> list[str]:
    return ["Result 1 text...", "Result 2 text..."]
```

When feeding tool results back to the API, you add a `function_call_output` item (after adding the model's `response.output` to the messages, so the call it answers is in the history):

```python
messages.append({
    "type": "function_call_output",
    "call_id": tool_call.call_id,   # links the result back to the request
    "output": json.dumps(results),  # must be a string
})
```

## Step-by-step

### 1. Define `SEARCH_TOOL`

Copy the tool definition from the recap above. The key parts are: `"type": "function"`, a `"name"`, a `"description"` (the model reads this to decide when to use it), and `"parameters"` describing what arguments it accepts.

### 2. Implement `handle_tool_call`

Parse the tool call's arguments (they come as a JSON string), call `search_fn`, and return the results as a JSON string:

```python
def handle_tool_call(tool_call, search_fn) -> str:
    args = json.loads(tool_call.arguments)
    if tool_call.name == "search_documents":
        results = search_fn(args["query"])
        return json.dumps(results)
    return json.dumps({"error": f"Unknown tool: {tool_call.name}"})
```

### 3. Implement `agentic_rag`

This is the agent loop. Start with a system message and the user's question, then loop:

```python
for _ in range(max_turns):
    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": "none"},
        input=messages,
        tools=[SEARCH_TOOL],
    )
    calls = [item for item in response.output if item.type == "function_call"]

    if not calls:
        return response.output_text  # done — model gave a final answer

    # Model wants to search — execute each tool call
    messages += response.output  # keep the model's function_call items in the history
    for tool_call in calls:
        result = handle_tool_call(tool_call, search_fn)
        messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": result,
        })
```

> **Important:** You must append the assistant's message (with the tool calls) to the conversation *before* appending the tool results. The API requires this ordering.

> **Important:** The `max_turns` parameter prevents infinite loops. If the model keeps searching without answering, you force a final completion after the loop ends.

## Try it

```bash
cd module-13-edge-topics/exercises/04-agentic-rag
python start.py
```

Try multi-part questions: "What is the status of the reactor AND what maintenance was done last week?", "Find all safety incidents and summarize them."

## Running Tests

```bash
pytest module-13-edge-topics/exercises/04-agentic-rag/test_start.py -v
```

## Stretch Goals

- Add a second tool (e.g., `get_document_by_id`) for the agent to fetch full documents.
- Log each tool call so you can watch the agent's reasoning process.
- Add a `/trace` command that shows the full message history.
