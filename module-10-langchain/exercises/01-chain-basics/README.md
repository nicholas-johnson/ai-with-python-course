# Exercise 1: Chain Basics

> **Scenario:** Hands-on work uses the **CSS Horizon** cargo survey vessel and sample reports below. Module demos use the **DSS Pathfinder** and `data/ship_logs.json` at the repo root.

## Recap

LangChain's core idea is **composable steps**. Instead of writing a function that builds a prompt string, calls the API, and parses the result, you snap three components together with the pipe (`|`) operator:

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

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

**OutputParser** — transforms the model's raw text into structured data:

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
```

**LCEL chain** — compose them with `|`:

```python
chain = prompt | model | parser
result = chain.invoke({"report": "Reactor coolant pressure dropped 15%."})
# {"category": "engineering", "summary": "...", "priority": "..."}
```

Each step receives the previous step's output. `prompt.invoke()` returns a `ChatPromptValue`, the model returns an `AIMessage`, the parser returns a `dict`. The pipe operator wires it all together.

## What you build

A console app in **`start.py`** that classifies crew reports using an LCEL chain and provides an interactive loop.

**Key functions:**

| Function | Description |
|---|---|
| `classify_report(report)` | Run the LCEL chain, return `{category, summary, priority}` |

## Step-by-step

### 1. Create the prompt template

Build a `ChatPromptTemplate` with:
- A **system message** that tells the model to classify reports into categories (`navigation`, `engineering`, `science`, `medical`, `operations`) and return JSON with `category`, `summary`, and `priority` (low/medium/high/critical).
- A **human message** with a `{report}` placeholder.

**Hint:** Tell the model to respond with *only* valid JSON — no markdown fences, no explanation.

### 2. Build the chain

Pipe three steps together:

```python
chain = prompt | model | parser
```

Use `ChatOpenAI(model="gpt-4o-mini", temperature=0)` for deterministic output and `JsonOutputParser()` to parse the JSON.

### 3. Implement `classify_report`

Call `chain.invoke({"report": report})` and return the resulting dict. The dict should have keys `category`, `summary`, and `priority`.

### 4. Build the interactive loop

Handle these commands:

| Command | Action |
|---|---|
| any text | Classify the report, show the result |
| `/stream` | Re-classify the last report with `.stream()` |
| `/raw` | Show the raw model output (before parsing) |
| `/batch` | Classify all `SAMPLE_REPORTS` in parallel with `chain.batch()` — shows timing |
| `/compare` | Run last report through both `JsonOutputParser` and `StrOutputParser` side-by-side |
| `quit` | Exit |

`/batch` demonstrates that LCEL chains are concurrency-ready out of the box — all reports are classified in a single batched call. `/compare` shows composability: same prompt, same model, swap the parser and the output type changes.

### 5. Show sample reports

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
- `classify_report` returns a dict with keys `category`, `summary`, `priority`

## Stretch goals

- Add a confidence score to the JSON schema
- Try `chain.abatch()` with a custom `max_concurrency` limit
- Add a `/time` command that compares sequential `invoke()` in a loop vs `batch()`
