# Exercise 1: Fact Extractor

## Recap

LLMs produce free text, but production systems need **structured data** -- typed fields your code can validate, compare, and aggregate. OpenAI supports structured outputs via `response_format={"type": "json_object"}`, which constrains the model to return valid JSON.

**Pydantic** models define the exact shape you want:

```python
from pydantic import BaseModel, Field

class Fact(BaseModel):
    subject: str = Field(description="The entity this fact is about")
    predicate: str = Field(description="The relationship or action")
    object: str = Field(description="The target entity or value")
    source_text: str = Field(description="The sentence this was extracted from")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
```

The extraction prompt instructs the LLM to return JSON matching the schema. Pydantic validates the response and raises clear errors when it doesn't match.

**Validation** filters low-confidence facts and deduplicates by `(subject, predicate, object)`, keeping the highest-confidence version.

## What you build

A console app in **`start.py`** that loads salvage mission logs from the derelict *Meridian*, extracts structured facts using OpenAI, and lets you explore the results interactively.

**Key functions:**

| Function | Description |
|---|---|
| `extract_facts(text, client)` | Prompt OpenAI with text + schema, parse JSON into `Fact` objects |
| `validate_facts(facts, threshold)` | Filter low-confidence, deduplicate by key triple |

## Step-by-step

### 1. Load the salvage logs

Load `data/derelict_logs.json` from the project root. Each entry has `id`, `content`, `author`, `category`. The logs document a salvage team investigating the derelict research ship *Meridian*, found adrift in the Tethys Nebula.

### 2. Define the `Fact` model

Use Pydantic with `subject`, `predicate`, `object`, `source_text`, and `confidence` fields. Add `Field(description=...)` to each -- these descriptions help the LLM understand what you want.

### 3. Implement `extract_facts`

Build a prompt that instructs the model to extract factual claims as JSON. Use `response_format={"type": "json_object"}` with `gpt-4o-mini`:

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": "Extract facts as JSON..."},
        {"role": "user", "content": text},
    ],
)
raw = json.loads(response.choices[0].message.content)
```

Parse the JSON array into `Fact` instances using `Fact.model_validate()`.

### 4. Implement `validate_facts`

Filter facts below the confidence threshold (default 0.7). Deduplicate by `(subject, predicate, object)` -- keep the one with the highest confidence.

### 5. Build the interactive loop

| Command | Action |
|---|---|
| any log ID (e.g. `SAL-001`) | Extract facts from that log |
| `/all` | Extract from all logs, show summary |
| `/validate` | Show only validated facts from the last extraction |
| `/json` | Show raw JSON from the last LLM response |
| `/schema` | Show the Pydantic schema |
| `quit` | Exit |

## Try it

```bash
cd module-06-structured-facts/exercises/01-fact-extractor
python start.py
```

Try extracting from different log IDs (SAL-001 through SAL-025). Compare the raw JSON with the validated facts. Notice how confidence varies by claim type — engineering measurements tend to score higher than speculative entries.

## Tests

```bash
pytest test_start.py -v
```

The tests check:
- `Fact` model validates correctly
- `extract_facts` returns a list of `Fact` objects
- `validate_facts` filters by confidence and deduplicates

## Stretch goals

- Try extracting with different prompts and compare fact quality
- Add entity type detection (person, system, location, event)
- Implement retry logic for malformed JSON responses
