"""FastAPI app — AI Recipe Finder with RAG, caching, guardrails, and tracing."""

import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import DATA_DIR
from .rag import build_index, hybrid_search, rerank, format_results
from .cache import SemanticCache
from .guardrails import check_allergens, redact_pii
from .vision import identify_ingredients
from .tracing import TraceContext

app = FastAPI(title="AI Recipe Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

recipes: list[dict] = []
collection = None
cache = SemanticCache()


class SearchRequest(BaseModel):
    query: str
    dietary_filter: str | None = None


class PhotoRequest(BaseModel):
    image_base64: str
    dietary_filter: str | None = None


@app.on_event("startup")
async def startup():
    """Load recipes.json and build the search index on startup.

    Steps:
    1. Load recipes from DATA_DIR/recipes.json
    2. Call build_index(recipes) and store the collection globally
    3. Print how many recipes were indexed
    """
    global recipes, collection
    # TODO: load recipes and build index


@app.get("/api/health")
async def health():
    """Return service health and index size.

    Returns: {"status": "ok", "index_size": N}
    """
    # TODO: return health status with collection count
    return {"status": "ok", "index_size": 0}


@app.post("/api/search")
async def search(req: SearchRequest):
    """Search for recipes matching a query.

    Steps:
    1. Create a TraceContext for this request
    2. Check the semantic cache first (trace it)
    3. If cache miss: run hybrid_search, apply dietary filter, rerank, format results
    4. Store results in cache
    5. Return {"results": [...], "cached": bool, "trace": trace.summary()}
    """
    trace = TraceContext()

    # TODO: implement traced search pipeline with caching

    return {"results": [], "cached": False, "trace": trace.summary()}


@app.post("/api/upload-photo")
async def upload_photo(req: PhotoRequest):
    """Accept a base64 image, identify ingredients, and search for matching recipes.

    Steps:
    1. Create a TraceContext
    2. Call identify_ingredients with the base64 image
    3. Use the identified ingredients as a search query
    4. Apply dietary filter if provided, rerank, and format results
    5. Return identified_ingredients, results, and trace
    """
    trace = TraceContext()

    # TODO: implement photo-based recipe search

    return {
        "identified_ingredients": "unknown",
        "results": [],
        "trace": trace.summary(),
    }


@app.get("/api/recipe/{recipe_id}")
async def get_recipe(recipe_id: str):
    """Return a full recipe by ID, with PII redacted from the description.

    Steps:
    1. Search the recipes list for a matching ID
    2. Apply redact_pii to the description field
    3. Return the recipe, or raise 404 if not found
    """
    # TODO: implement recipe lookup with PII redaction
    raise HTTPException(status_code=404, detail="Recipe not found")
