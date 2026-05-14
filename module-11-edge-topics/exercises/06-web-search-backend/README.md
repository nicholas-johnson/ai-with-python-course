# Exercise 06 — Web Search Backend

## Recap

Internal knowledge bases have limited scope. A **web search backend** adds live internet search as a fallback when internal results are insufficient. DuckDuckGo provides a free search option. The key is normalising web results into the same format as internal results so the generation pipeline is source-agnostic.

## Your Task

1. Implement `web_search(query, max_results)` — search DuckDuckGo and parse results.
2. Implement `format_web_results(raw_results)` — normalise into standard passage format.
3. Implement `search_with_fallback(query, vector_search_fn, threshold)` — try internal first, fall back to web.

## Steps

1. Open `start.py` and review the function signatures.
2. Implement `web_search`: construct a DuckDuckGo URL, fetch HTML, parse result titles and snippets.
3. Implement `format_web_results`: convert raw results into `{"text": ..., "source": ..., "url": ...}` dicts.
4. Implement `search_with_fallback`: check internal search confidence, fall back to web if too low.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/06-web-search-backend/test_start.py -v
```

## Stretch Goals

- Merge internal and web results instead of falling back.
- Add result deduplication across sources.
- Cache web search results to avoid repeated queries.
