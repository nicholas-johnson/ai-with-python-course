# Exercise 1: Chain Basics

> **Scenario:** Hands-on work uses the **CSS Horizon** cargo survey vessel and sample reports below. Module demos use the **DSS Pathfinder** and `data/ship_logs.json` at the repo root.

## Recap

LangChain's core idea is **composable steps**. Instead of writing a function that builds a prompt string, calls the API, and parses the result, you snap components together with the pipe (`|`) operator:

**PromptTemplate** — a reusable prompt with `{variables}`:

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify reports as: navigation, engineering, science, medical, operations."),
    ("human", "{report}"),
])
```

**ChatModel** — the LLM wrapper:

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
```

**Structured output** — describe the result as a Pydantic model and let the model fill it in:

```python
from typing import Literal
from pydantic import BaseModel, Field

class Classification(BaseModel):
    category: Literal["navigation", "engineering", "science", "medical", "operations"]
    summary: str = Field(description="One-sentence summary of the report")
    priority: Literal["low", "medium", "high", "critical"]

structured_model = model.with_structured_output(Classification)
```

`with_structured_output` sends the schema to the provider, which constrains the response to it. The `Literal` fields mean you can't get back a category that isn't on the list, and you don't need "respond with ONLY JSON" in your prompt.

**LCEL chain** — compose them with `|`:

```python
chain = prompt | structured_model
result = chain.invoke({"report": "Reactor coolant pressure dropped 15%."})
# Classification(category='engineering', summary='...', priority='high')
```

Each step receives the previous step's output. `prompt.invoke()` returns a `ChatPromptValue`, and the structured model returns a `Classification` instance. The pipe operator wires it all together.

**OutputParsers** — the older way to get structure is to *ask* for JSON in the prompt and parse the text: `prompt | model | JsonOutputParser()`. It still has one advantage: it streams a partial dict as the JSON arrives, whereas structured output arrives as one complete object. `StrOutputParser()` just returns the text.

## What you build

A console app in **`start.py`** that classifies crew reports using an LCEL chain and provides an interactive loop.

**Key functions:**

| Function | Description |
|---|---|
| `Classification` | Pydantic model describing the result |
| `classify_report(report)` | Run the LCEL chain, return `{category, summary, priority}` as a dict |

## Step-by-step

### 1. Define the schema

Write the `Classification` Pydantic model shown above. Use `Literal` for `category` and `priority` so only the allowed values are accepted.

### 2. Create the prompt template

Build a `ChatPromptTemplate` with:
- A **system message** that tells the model to classify the crew report: choose a category, write a one-sentence summary, and set the priority.
- A **human message** with a `{report}` placeholder.

You don't need to describe the JSON format — the schema does that.

### 3. Build the chain

```python
model = ChatOpenAI(model=MODEL, reasoning_effort="none", temperature=0)
chain = prompt | model.with_structured_output(Classification)
```

### 4. Implement `classify_report`

Call `chain.invoke({"report": report})`. It returns a `Classification`; return `result.model_dump()` so callers get a plain dict with `category`, `summary`, and `priority`.

### 5. Build the interactive loop

Handle these commands:

| Command | Action |
|---|---|
| any text | Classify the report, show the result |
| `/stream` | Re-classify the last report with `.stream()` on a `JsonOutputParser` chain — watch the dict fill in |
| `/raw` | Show the raw model output (`prompt \| model \| StrOutputParser()`) |
| `/batch` | Classify all `SAMPLE_REPORTS` in parallel with `chain.batch()` — shows timing |
| `/compare` | Run the last report through structured output, `JsonOutputParser`, and `StrOutputParser` side-by-side |
| `quit` | Exit |

`/batch` demonstrates that LCEL chains are concurrency-ready out of the box — all reports are classified in a single batched call. `/compare` shows composability: same prompt, same model, swap the last step and the output type changes.

**Hint:** a parser chain needs the prompt to ask for JSON. You can extend a template with `json_prompt = prompt + ("system", "Respond with ONLY a JSON object ...")`.

### 6. Show sample reports

Define a `SAMPLE_REPORTS` list with a few hardcoded example reports and display them at startup so the learner can copy/paste them into the prompt.

## Try it

```bash
cd module-10-langchain/exercises/01-chain-basics
python start.py
```

Try classifying different types of reports — engineering faults, navigation updates, medical emergencies, science observations.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `Classification` rejects a category that isn't in the list
- `classify_report` returns a dict whose `category` and `priority` are allowed values (integration test — runs when `OPENAI_API_KEY` is set)

## Stretch goals

- Add a `confidence: float = Field(ge=0, le=1)` field to the schema
- Try `chain.abatch()` with a custom `max_concurrency` limit
- Add a `/time` command that compares sequential `invoke()` in a loop vs `batch()`
