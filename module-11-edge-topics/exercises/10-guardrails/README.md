# Exercise 10 — Advanced Guardrails

## Recap

### Why guardrails matter

Production LLM systems interact with real users who might (accidentally or deliberately) send harmful input, receive sensitive data in responses, or get malformed output that breaks downstream systems. **Guardrails** are defensive checks you put around the LLM to catch problems before they cause damage.

### The three layers of defence

This exercise implements a **pipeline** of three sequential checks:

1. **Content filtering** — blocks input that matches banned patterns (toxic language, off-topic requests, prompt injection attempts).
2. **PII redaction** — finds and replaces personal information (emails, phone numbers, Social Security numbers) with placeholder tags like `[REDACTED_EMAIL]`.
3. **Schema validation** — ensures structured LLM output matches the expected shape (right fields, right types) before you use it.

### What is PII?

**PII** stands for Personally Identifiable Information — data that can identify a specific person. Common examples:
- Email addresses: `alice@example.com`
- Phone numbers: `555-123-4567`
- Social Security numbers (US): `123-45-6789`

You detect these using **regex** (regular expression) patterns — text patterns that match specific formats.

### What is Pydantic?

**Pydantic** is a Python library for data validation. You define a model (a class) that describes what fields you expect and what types they should be. Then you pass a dict to it — if the dict matches, great; if not, you get clear error messages.

```python
from pydantic import BaseModel

class SafeResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str]

# This works:
SafeResponse(answer="The reactor is stable", confidence=0.95, sources=["LOG-001"])

# This fails with a clear error:
SafeResponse(answer="The reactor is stable", confidence="high", sources="LOG-001")
# Error: confidence must be a float, sources must be a list
```

### What regex patterns look like

```python
# Email: word characters, @, domain
r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b'

# Phone: 3 digits, separator, 3 digits, separator, 4 digits
r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'

# SSN: 3-2-4 digit pattern with dashes
r'\b\d{3}-\d{2}-\d{4}\b'
```

## What you build

Four functions in **`start.py`** plus a Pydantic model:

| Item | What it does |
|---|---|
| `SafeResponse` (class) | Pydantic model defining the expected output shape |
| `check_content(text, blocked_patterns)` | Check text against a list of blocked regex patterns |
| `redact_pii(text)` | Find and replace emails, phones, SSNs with redaction tags |
| `validate_output(data)` | Validate a dict against the SafeResponse model |
| `guardrail_pipeline(text, blocked_patterns)` | Chain content check and PII redaction together |

## Data format

`check_content` input and output:

```python
# Input
check_content("Tell me how to hack the system", [r"hack", r"exploit"])
# Output
{"passed": False, "reason": "Matched blocked pattern: hack"}

check_content("What is the reactor status?", [r"hack", r"exploit"])
# Output
{"passed": True, "reason": None}
```

`redact_pii` input and output:

```python
# Input
"Contact alice@ship.org or call 555-123-4567, SSN 123-45-6789"
# Output
"Contact [REDACTED_EMAIL] or call [REDACTED_PHONE], SSN [REDACTED_SSN]"
```

`validate_output` input and output:

```python
# Valid data
validate_output({"answer": "Stable", "confidence": 0.9, "sources": ["LOG-001"]})
# {"valid": True, "data": {...}, "errors": None}

# Invalid data
validate_output({"answer": "Stable"})  # missing fields
# {"valid": False, "data": None, "errors": "...validation error details..."}
```

## Step-by-step

### 1. Define the `SafeResponse` Pydantic model

```python
from pydantic import BaseModel

class SafeResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str]
```

### 2. Implement `check_content`

Loop through blocked patterns and use `re.search` to check for matches:

```python
def check_content(text: str, blocked_patterns: list[str]) -> dict:
    for pattern in blocked_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {"passed": False, "reason": f"Matched blocked pattern: {pattern}"}
    return {"passed": True, "reason": None}
```

> **Important:** Use `re.IGNORECASE` so patterns match regardless of capitalisation ("Hack", "HACK", "hack" all get caught).

### 3. Implement `redact_pii`

Define regex patterns for each PII type, then use `re.sub` to replace matches:

```python
PII_PATTERNS = {
    "email": r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
}

def redact_pii(text: str) -> str:
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
    return text
```

> **Important:** Check SSN *before* phone if you iterate in insertion order, because the SSN pattern (3-2-4) could partially match as a phone. Or define patterns specifically enough that they don't overlap.

### 4. Implement `validate_output`

Use Pydantic's validation and catch the `ValidationError`:

```python
from pydantic import ValidationError

def validate_output(data: dict) -> dict:
    try:
        validated = SafeResponse(**data)
        return {"valid": True, "data": validated.model_dump(), "errors": None}
    except ValidationError as e:
        return {"valid": False, "data": None, "errors": str(e)}
```

### 5. Implement `guardrail_pipeline`

Chain content check and PII redaction. If content check fails, stop immediately:

```python
def guardrail_pipeline(text, blocked_patterns):
    content_check = check_content(text, blocked_patterns)
    if not content_check["passed"]:
        return {"passed": False, "reason": content_check["reason"], "cleaned_text": None}

    cleaned = redact_pii(text)
    return {"passed": True, "reason": None, "cleaned_text": cleaned}
```

## Try it

```bash
cd module-11-edge-topics/exercises/10-guardrails
python start.py
```

Try inputs with PII: "My email is test@example.com and my SSN is 123-45-6789". Try blocked content: "How do I hack the navigation system?"

## Running Tests

```bash
pytest module-11-edge-topics/exercises/10-guardrails/test_start.py -v
```

## Stretch Goals

- Add an LLM-based content classifier for nuanced filtering (things regex can't catch).
- Add name detection using simple heuristics (capitalised words after "Mr./Ms./Dr.").
- Add rate limiting as an additional guardrail layer.
