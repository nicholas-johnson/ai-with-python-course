"""
Module 3 Demo — TV Ratings MCP Server
A local stdio MCP server that looks up star ratings for TV shows.

Run directly:  python tv_server.py   (starts an MCP stdio server)
Used by:       test_tv_server.py and demo.py (part 5) connect to this server.

Ratings come from TVMaze (https://api.tvmaze.com). No API key.
Scores are out of 10 there; this server also reports them as stars out of 5.
"""

import json
import logging
import sys

import httpx
from mcp.server.mcpserver import MCPServer

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

server = MCPServer("TV Ratings")

SEARCH_URL = "https://api.tvmaze.com/search/shows"
TIMEOUT = 10.0
USER_AGENT = "pathfinder-tv-mcp/1.0 (ai-python-course demo)"


def _error(message: str) -> str:
    return json.dumps({"error": message})


def _stars(score: float | None) -> float | None:
    if score is None:
        return None
    # Half-up to one decimal. 8.5/10 becomes 4.3 stars, not 4.2.
    return round(score / 2 + 1e-6, 1)


def _network(show: dict) -> str | None:
    channel = show.get("network") or show.get("webChannel") or {}
    return channel.get("name")


def _country(show: dict) -> str | None:
    channel = show.get("network") or show.get("webChannel") or {}
    country = channel.get("country") or {}
    return country.get("name")


def _record(show: dict) -> dict:
    score = (show.get("rating") or {}).get("average")
    return {
        "title": show.get("name"),
        "stars": _stars(score),
        "out_of": 5,
        "score": score,
        "score_out_of": 10,
        "premiered": show.get("premiered"),
        "status": show.get("status"),
        "network": _network(show),
        "country": _country(show),
        "genres": show.get("genres") or [],
    }


def _search(client: httpx.Client, title: str) -> list[dict]:
    response = client.get(SEARCH_URL, params={"q": title})
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool()
def get_show_rating(title: str) -> str:
    """Get the star rating for a TV show by title.

    title: show name, such as "Breaking Bad" or "The Office".
    Returns stars out of 5 for the best match, plus other close matches.
    """
    title = title.strip()
    if not title:
        return _error("title is required")

    try:
        headers = {"User-Agent": USER_AGENT}
        with httpx.Client(timeout=TIMEOUT, headers=headers) as client:
            matches = _search(client, title)
    except httpx.HTTPStatusError as exc:
        return _error(f"Show lookup failed ({exc.response.status_code})")
    except httpx.HTTPError:
        return _error("Show lookup failed: could not reach the ratings service")

    shows = [item.get("show") or {} for item in matches if item.get("show")]
    if not shows:
        return _error(f"Could not find a TV show named {title!r}")

    return json.dumps({
        "query": title,
        "match": _record(shows[0]),
        "other_matches": [_record(show) for show in shows[1:4]],
    })


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("TV ratings MCP server starting…", file=sys.stderr)
    server.run()
