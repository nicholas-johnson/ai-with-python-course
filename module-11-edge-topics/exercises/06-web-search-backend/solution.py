"""
Exercise 06 — Web Search Backend (Solution)

Use web search as a fallback retrieval source when internal
search results are insufficient.
"""

import re
from urllib.parse import quote_plus
import httpx


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo and return parsed results.
    """
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RAGBot/1.0)"}

    response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10)
    response.raise_for_status()

    results = []
    result_blocks = re.findall(
        r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
        r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
        response.text,
        re.DOTALL,
    )

    for href, title_html, snippet_html in result_blocks[:max_results]:
        title = re.sub(r"<[^>]+>", "", title_html).strip()
        snippet = re.sub(r"<[^>]+>", "", snippet_html).strip()
        if title:
            results.append({
                "title": title,
                "snippet": snippet,
                "url": href,
            })

    return results[:max_results]


def format_web_results(raw_results: list[dict]) -> list[dict]:
    """
    Normalise web search results into the standard passage format.
    """
    formatted = []
    for result in raw_results:
        formatted.append({
            "text": f"{result['title']}. {result['snippet']}",
            "source": "web",
            "url": result["url"],
        })
    return formatted


def search_with_fallback(
    query: str,
    vector_search_fn,
    threshold: float = 0.7,
) -> dict:
    """
    Search internal vector store first, fall back to web if confidence is low.
    """
    internal_results = vector_search_fn(query)

    if internal_results and internal_results[0].get("score", 0) >= threshold:
        return {
            "source": "internal",
            "results": internal_results,
        }

    raw_web = web_search(query)
    formatted = format_web_results(raw_web)
    return {
        "source": "web",
        "results": formatted,
    }
