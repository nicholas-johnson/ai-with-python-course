"""
Exercise 06 — Web Search Backend

Use web search as a fallback retrieval source when internal
search results are insufficient.
"""

import re
from urllib.parse import quote_plus
import httpx


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo and return parsed results.

    Each result should be a dict with keys: "title", "snippet", "url".

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of result dicts.

    TODO:
    - Build the DuckDuckGo HTML search URL
    - Fetch the page with httpx (set a User-Agent header)
    - Parse the HTML to extract result titles, snippets, and URLs
    - Return up to max_results results
    """
    # TODO: implement web search
    pass


def format_web_results(raw_results: list[dict]) -> list[dict]:
    """
    Normalise web search results into the standard passage format.

    Input dicts have: "title", "snippet", "url"
    Output dicts should have: "text", "source", "url"

    Where "text" combines the title and snippet, and "source" is "web".

    TODO:
    - For each result, create a new dict with:
      - "text": "{title}. {snippet}"
      - "source": "web"
      - "url": the original URL
    """
    # TODO: implement result formatting
    pass


def search_with_fallback(
    query: str,
    vector_search_fn,
    threshold: float = 0.7,
) -> dict:
    """
    Search internal vector store first, fall back to web if confidence is low.

    Args:
        query: The user's question.
        vector_search_fn: Function(query) -> list[dict] where each dict
            has "text" and "score" keys.
        threshold: Minimum score to consider internal results sufficient.

    Returns:
        Dict with:
        - "source": "internal" or "web"
        - "results": list of result dicts

    TODO:
    - Call vector_search_fn to get internal results
    - If the top result's score >= threshold, return internal results
    - Otherwise, call web_search and format the results
    - Return the results with a "source" indicator
    """
    # TODO: implement fallback logic
    pass
