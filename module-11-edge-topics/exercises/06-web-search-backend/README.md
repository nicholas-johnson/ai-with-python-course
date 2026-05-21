# Exercise 06 — Web Search Backend

## Recap

### The problem: your knowledge base has gaps

Your internal vector store only knows what you've put into it. When a user asks about something outside that scope — breaking news, niche topics, or anything you haven't indexed — the retrieval step returns low-confidence garbage and the LLM hallucinates an answer.

### The solution: fall back to web search

A **web search backend** gives your RAG system a second retrieval source. The strategy is:

1. Try your internal vector search first.
2. Check the confidence of the results (the similarity score).
3. If confidence is below a threshold, fall back to a web search.
4. Normalise web results into the same format as internal results so the rest of your pipeline doesn't need to care where the results came from.

### DuckDuckGo as a free search API

DuckDuckGo has an HTML endpoint that returns search results you can scrape. No API key needed:

```python
from urllib.parse import quote_plus
import httpx

url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
response = httpx.get(url, headers={"User-Agent": "Mozilla/5.0 ..."})
# Parse the HTML to extract titles, snippets, and URLs
```

You then parse the results using regex to find result links and snippet text.

### Normalised result format

Your pipeline expects results in a standard shape regardless of source:

```python
{
    "text": "Title of the result. Snippet text from the page...",
    "source": "web",       # or "internal"
    "url": "https://..."   # only for web results
}
```

## What you build

Three functions in **`start.py`**:

| Function | What it does |
|---|---|
| `web_search(query, max_results)` | Hit DuckDuckGo, parse HTML, return raw results |
| `format_web_results(raw_results)` | Normalise raw results into the standard passage format |
| `search_with_fallback(query, vector_search_fn, threshold)` | Try internal first, fall back to web if confidence is low |

## Data format

Raw web search results (before normalisation):

```python
[
    {"title": "Reactor Safety Guide", "snippet": "Overview of protocols...", "url": "https://..."},
    {"title": "Engineering Handbook", "snippet": "Chapter 7 covers...", "url": "https://..."},
]
```

After `format_web_results`, each becomes:

```python
{"text": "Reactor Safety Guide. Overview of protocols...", "source": "web", "url": "https://..."}
```

The `search_with_fallback` function returns a dict indicating which source was used:

```python
{"source": "internal", "results": [...]}  # if internal results were good enough
{"source": "web", "results": [...]}       # if we fell back to the web
```

## Step-by-step

### 1. Implement `web_search`

Build the DuckDuckGo URL, make an HTTP GET request, and parse results from the HTML:

```python
def web_search(query: str, max_results: int = 5) -> list[dict]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RAGBot/1.0)"}

    response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10)
    response.raise_for_status()

    # Parse with regex — look for result links and snippets
    ...
```

**Hint** — DuckDuckGo results have CSS classes `result__a` (for the link/title) and `result__snippet` (for the description). Use `re.findall` with a pattern that captures both.

> **Important:** Always set a `User-Agent` header and a timeout. Without them, the request may be blocked or hang indefinitely.

### 2. Implement `format_web_results`

Combine title and snippet into a single `"text"` field, set `"source"` to `"web"`, and keep the URL:

```python
def format_web_results(raw_results: list[dict]) -> list[dict]:
    formatted = []
    for result in raw_results:
        formatted.append({
            "text": f"{result['title']}. {result['snippet']}",
            "source": "web",
            "url": result["url"],
        })
    return formatted
```

### 3. Implement `search_with_fallback`

Call the internal search first. Check the score of the top result against the threshold. If it's high enough, return internal results. Otherwise, do a web search:

```python
def search_with_fallback(query, vector_search_fn, threshold=0.7):
    internal_results = vector_search_fn(query)

    if internal_results and internal_results[0].get("score", 0) >= threshold:
        return {"source": "internal", "results": internal_results}

    raw_web = web_search(query)
    formatted = format_web_results(raw_web)
    return {"source": "web", "results": formatted}
```

## Try it

```bash
cd module-11-edge-topics/exercises/06-web-search-backend
python start.py
```

Try queries your internal store won't have: "latest Python release", "SpaceX launch schedule", "DuckDuckGo API documentation".

## Running Tests

```bash
pytest module-11-edge-topics/exercises/06-web-search-backend/test_start.py -v
```

## Stretch Goals

- Merge internal and web results instead of choosing one or the other.
- Add result deduplication across sources (same URL = same result).
- Cache web search results to avoid repeated queries (even a simple dict cache helps).
