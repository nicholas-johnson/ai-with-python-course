# Module 10 — LangChain with Python

> LangChain packages common AI patterns into composable building blocks. Prompt templates, tool agents, RAG pipelines — the same things you built by hand, but with less boilerplate. This module teaches you to use LangChain practically: build a chain, add tools, add retrieval. Each exercise builds on the last, so by the end you have a working RAG agent assembled from LangChain components.

## Learning goals

- Build **LCEL chains**: prompt templates, output parsers, and the pipe operator.
- Wrap functions as **LangChain tools** and run them with **`create_agent`** (LangChain 1.x).
- Construct a **RAG chain** with a LangChain retriever and ChromaDB.
- Serve an LCEL chain as a REST API with **FastAPI** using the Runnable `ainvoke` / `astream` methods.
- Know when to use LangChain and when to stay hand-rolled.

---

## LangChain building blocks

LangChain organises AI applications into composable components. Each component does one thing and connects to the next through a standard interface.

**PromptTemplate** — a string template with placeholders. Separates prompt logic from data.

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Pathfinder mission analyst."),
    ("human", "Classify this report: {report}"),
])
```

**ChatModel** — the LLM wrapper. Handles API details, retries, and token counting.

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
```

**OutputParser** — transforms the model's raw text into structured data. `JsonOutputParser` extracts JSON, `StrOutputParser` passes text through.

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
```

---

## LCEL — LangChain Expression Language

LCEL lets you compose components with the pipe (`|`) operator. Data flows left to right: prompt → model → parser.

```python
chain = prompt | model | parser
result = chain.invoke({"report": "Reactor coolant pressure dropped 15%."})
# {"category": "engineering", "severity": "medium", "summary": "..."}
```

Under the hood, `|` creates a `RunnableSequence`. Each component receives the previous one's output. This is the same pipeline pattern you built by hand in earlier modules — LangChain standardises the interface.

LCEL chains are:
- **Composable** — snap components together like Lego.
- **Streamable** — call `.stream()` instead of `.invoke()` for token-by-token output.
- **Batchable** — call `.batch()` for parallel processing.

---

## Tool-calling agents

LangChain wraps the tool-calling loop from Module 2 into `create_agent`. You define tools, create an agent, and run it — the framework handles the loop, tool dispatch, and error recovery. In LangChain 1.x the agent runs on LangGraph, so it also supports middleware (human-in-the-loop, retries, summarisation) and checkpointed memory.

```python
from langchain_core.tools import tool
from langchain.agents import create_agent

@tool
def read_sensor(sensor_name: str) -> str:
    """Read the current value of a ship sensor."""
    return json.dumps(SENSOR_DATA.get(sensor_name, {"error": "Unknown sensor"}))

@tool
def query_crew(department: str) -> str:
    """Look up crew members by department."""
    results = [c for c in CREW if c["department"] == department]
    return json.dumps(results)

tools = [read_sensor, query_crew]
agent = create_agent(model, tools, system_prompt="You are the DSS Pathfinder AI assistant.")

result = agent.invoke({"messages": [{"role": "user", "content": "What is the reactor temperature?"}]})
answer = result["messages"][-1].text
```

Use `.text` rather than `.content` to read a reply. When you give `gpt-6-*` models tools, `ChatOpenAI` switches to the Responses API, and `.content` comes back as a list of content blocks. `.text` always gives you a plain string.

The `@tool` decorator generates the JSON Schema from the function's type hints and docstring — same pattern as the `ToolRegistry` you built in Module 2, but standardised. `result["messages"]` contains every tool call and tool result, so you can print the full trace.

> **Upgrading from LangChain 0.x?** `AgentExecutor`, `create_tool_calling_agent`, and the legacy chains (`RetrievalQA`, `LLMChain`) moved to the `langchain-classic` package in 1.0. Use `create_agent` for new code.

---

## RAG chains with LCEL

LangChain's retrieval chain follows the same pattern from Module 5, but with less boilerplate:

```python
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def format_docs(docs):
    return "\n\n".join(
        f"[Source {i+1}] {doc.page_content}"
        for i, doc in enumerate(docs)
    )

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

answer = rag_chain.invoke("What caused the reactor anomaly?")
```

`RunnablePassthrough` passes the input through unchanged (the question). The retriever runs in parallel, fetches documents, and `format_docs` formats them for the prompt. The chain reads naturally: retrieve context, build prompt, call model, parse output.

---

## Serving chains as APIs

Every LCEL chain is a Runnable with async `ainvoke`, `abatch`, and `astream`. Exposing one over HTTP is a thin FastAPI route:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class ReportInput(BaseModel):
    report: str

class InvokeRequest(BaseModel):
    input: ReportInput

app = FastAPI(title="Report API")

@app.post("/classify/invoke")
async def classify_invoke(req: InvokeRequest):
    return {"output": await chain.ainvoke(req.input.model_dump())}

# POST /classify/invoke  {"input": {"report": "..."}}
```

Older material uses LangServe's `add_routes` for this. LangServe is no longer maintained and conflicts with current dependencies, so the course writes the routes directly. For deploying agents, LangChain points to [LangGraph](https://langchain-ai.github.io/langgraph/) / LangSmith deployment.

---

## When to use LangChain vs. hand-rolled

LangChain accelerates development when you are building standard patterns (RAG, tool agents, chains). But it adds a dependency and an abstraction layer that can obscure what is happening.

| | LangChain | Hand-rolled |
|-|-----------|-------------|
| **Speed to prototype** | Fast — standard patterns are pre-built | Slower — you write every component |
| **Flexibility** | Constrained by framework abstractions | Full control over every detail |
| **Debugging** | Harder — errors originate inside framework code | Easier — you wrote it, you debug it |
| **Dependencies** | Large dependency tree | Minimal — just `openai` and your code |
| **Learning value** | Hides mechanics | Teaches fundamentals |

The recommendation: **know the pattern first, then use the framework**. You can debug a LangChain chain because you know what it does under the hood.

---

## Field rules

- **Know the pattern, then pick the tool.** LangChain is faster only if you know what it does underneath.
- **Use LCEL for standard pipelines.** Prompt → model → parser is one line.
- **Inspect `result["messages"]` during development** (or turn on LangSmith tracing). The trace shows every tool call and decision.
- **Know when to eject.** If the framework fights you, go back to plain Python.

---

## Demos

```bash
python module-10-langchain/demo/01_chains_and_prompts.py
python module-10-langchain/demo/02_langchain_agents.py
python module-10-langchain/demo/03_langchain_rag.py
python module-10-langchain/demo/04_serving_chains.py
python module-10-langchain/demo/04_serving_chains.py serve   # live server
```

## Exercises

**Demos vs exercises:** Demos use the **DSS Pathfinder** and shared repo data (`data/ship_logs.json`, `data/crew.json`). Exercises use the **CSS Horizon** cargo survey vessel and local data in [`exercises/data/`](exercises/data/) (`horizon_logs.json`, `horizon_crew.json`) — same LangChain patterns, different scenario so you apply what you saw in the demo rather than copy it verbatim.

Exercises 01–03 chain together; exercise 04 is standalone (same LCEL pattern as 01, exposed over HTTP).

| Folder | What you build |
| ------ | -------------- |
| [`exercises/01-chain-basics`](exercises/01-chain-basics/) | LCEL chain that classifies crew reports into category, summary, and priority. |
| [`exercises/02-tool-agent`](exercises/02-tool-agent/) | Tool agent that wraps the classifier from 01 + ship tools with `create_agent`. |
| [`exercises/03-rag-chain`](exercises/03-rag-chain/) | RAG chain that adds retrieval over ship logs to the agent from 02. |
| [`exercises/04-chain-api`](exercises/04-chain-api/) | FastAPI service exposing the classifier chain at `/classify/invoke`, plus a health check. |

Run tests for this module:

```bash
pytest module-10-langchain/
```

## Slides

From repo root: `pnpm slides:10`, or `cd module-10-langchain/slides && pnpm dev`.

## Reference

- [LangChain Python docs](https://python.langchain.com/)
- [LCEL — LangChain Expression Language](https://python.langchain.com/docs/concepts/lcel/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangSmith (tracing)](https://smith.langchain.com/)
- [LangChain 1.0 agents (`create_agent`)](https://docs.langchain.com/oss/python/langchain/agents)
