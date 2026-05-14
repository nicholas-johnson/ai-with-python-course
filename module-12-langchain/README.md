# Module 12 — LangChain with Python

> You have built agents from scratch — loops, registries, memory stores, RAG pipelines. Now meet LangChain, the framework that packages these patterns into reusable components. LangChain is not magic; it is the same concepts you already know wrapped in a consistent API. This module teaches you the framework's building blocks, when to use them, and when to roll your own.

## Learning goals

- Understand LangChain's building blocks: **chains**, **prompt templates**, **output parsers**, **LCEL**.
- Build a **tool-calling agent** with `create_tool_calling_agent` and `AgentExecutor`.
- Construct **RAG chains** with `RetrievalQA` and LCEL.
- Evaluate the **trade-offs** between LangChain and hand-rolled solutions.

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

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
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

LangChain wraps the tool-calling loop from Module 3 into `AgentExecutor`. You define tools, create an agent, and run it — the framework handles the loop, tool dispatch, and error recovery.

```python
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor

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
agent = create_tool_calling_agent(model, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "What is the reactor temperature?"})
```

The `@tool` decorator generates the JSON Schema from the function's type hints and docstring — same pattern as the `ToolRegistry` you built in Module 3, but standardised. `verbose=True` prints the thought/action/observation trace.

---

## RAG chains with LCEL

LangChain's retrieval chain follows the same pattern from Module 6, but with less boilerplate:

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

## When to use LangChain vs. hand-rolled

LangChain accelerates development when you are building standard patterns (RAG, tool agents, chains). But it adds a dependency and an abstraction layer that can obscure what is happening.

| | LangChain | Hand-rolled |
|-|-----------|-------------|
| **Speed to prototype** | Fast — standard patterns are pre-built | Slower — you write every component |
| **Flexibility** | Constrained by framework abstractions | Full control over every detail |
| **Debugging** | Harder — errors originate inside framework code | Easier — you wrote it, you debug it |
| **Dependencies** | Large dependency tree | Minimal — just `openai` and your code |
| **Learning value** | Hides mechanics | Teaches fundamentals |

The recommendation: **understand the fundamentals first** (Modules 1-11), then use LangChain to accelerate production work. You can debug a LangChain chain because you know what it does under the hood.

---

## Field rules

- **Learn the loop before the framework.** LangChain is the tool-calling loop, abstracted.
- **Use LCEL for standard pipelines.** Prompt → model → parser is one line.
- **Keep `verbose=True` during development.** The trace shows every tool call and decision.
- **Know when to eject.** If the framework fights you, go back to plain Python.

---

## Demos

```bash
python module-12-langchain/demo/01_chains_and_prompts.py
python module-12-langchain/demo/02_langchain_agents.py
python module-12-langchain/demo/03_langchain_rag.py
```

## Exercises

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-chain-basics`](exercises/01-chain-basics/) | Build an LCEL chain: prompt → model → JSON parser. |
| [`exercises/02-tool-agent`](exercises/02-tool-agent/) | Wrap ship tools with `@tool` and run them via `AgentExecutor`. |
| [`exercises/03-rag-chain`](exercises/03-rag-chain/) | Build a RAG chain with LCEL: retriever → prompt → model → answer. |

Run tests for this module:

```bash
pytest module-12-langchain/
```

## Slides

From repo root: `pnpm slides:12`, or `cd module-12-langchain/slides && pnpm dev`.

## Reference

- [LangChain Python docs](https://python.langchain.com/)
- [LCEL — LangChain Expression Language](https://python.langchain.com/docs/concepts/lcel/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangSmith (tracing)](https://smith.langchain.com/)
