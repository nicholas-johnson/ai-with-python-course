# Extras — Capstone Projects

Full-stack capstone apps that pull the whole course together. Do them **after Module 13**: every capstone uses production patterns from **Module 12** (tracing, reliability, cost controls) together with techniques from **Module 13** (hybrid search, re-ranking, semantic caching, guardrails, text-to-SQL, agentic RAG).

Pick one. Each capstone provides a SvelteKit frontend; you build the FastAPI backend in `starter/`. A reference implementation lives in `solution/`.

| # | Capstone | Directory | Key techniques |
|---|----------|-----------|----------------|
| 1 | AI Recipe Finder | [`01-recipe-finder/`](01-recipe-finder/) | RAG, hybrid search, reranking, multimodal vision, allergen guardrails |
| 2 | AI Movie Night | [`02-movie-night/`](02-movie-night/) | RAG, text-to-SQL, reranking, semantic cache, chart data |
| 3 | AI Travel Planner | [`03-travel-planner/`](03-travel-planner/) | Agentic RAG, tool calling, structured itineraries, web fallback |
| 4 | AI Personal Assistant | [`04-personal-assistant/`](04-personal-assistant/) | Chat + tools + MCP, RAG over notes, calendar, cost controls |

Want something open-ended instead? [`capstone-ideas.md`](capstone-ideas.md) lists project ideas built on Hugging Face models running on CPU — no starter code, no tests.

## Running the tests

Each capstone's tests run against its reference solution:

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
cd extras/01-recipe-finder
pytest tests/

# Option B - uv (no activation needed):
cd extras/01-recipe-finder
uv run --extra dev pytest tests/
```
