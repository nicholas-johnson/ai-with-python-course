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
    global recipes, collection
    recipes_path = os.path.join(DATA_DIR, "recipes.json")
    with open(recipes_path) as f:
        recipes = json.load(f)
    collection, _ = build_index(recipes)
    print(f"Indexed {collection.count()} recipes.")


@app.get("/api/health")
async def health():
    count = collection.count() if collection else 0
    return {"status": "ok", "index_size": count}


@app.post("/api/search")
async def search(req: SearchRequest):
    trace = TraceContext()

    span = trace.start_span("cache_lookup")
    cached = cache.get(req.query)
    trace.end_span(span, metadata={"hit": cached is not None})

    if cached:
        return {"results": cached, "cached": True, "trace": trace.summary()}

    span = trace.start_span("hybrid_search")
    hits = hybrid_search(req.query, collection)
    trace.end_span(span, metadata={"count": len(hits)})

    if req.dietary_filter:
        span = trace.start_span("dietary_filter")
        hits = [
            h for h in hits
            if req.dietary_filter.lower() in h.get("metadata", {}).get("dietary", "").lower()
        ]
        trace.end_span(span, metadata={"remaining": len(hits)})

    span = trace.start_span("rerank")
    hits = rerank(req.query, hits)
    trace.end_span(span, metadata={"count": len(hits)})

    span = trace.start_span("format")
    results = format_results(hits)
    trace.end_span(span)

    cache.set(req.query, results)

    return {"results": results, "cached": False, "trace": trace.summary()}


@app.post("/api/upload-photo")
async def upload_photo(req: PhotoRequest):
    trace = TraceContext()

    span = trace.start_span("identify_ingredients")
    ingredients_text = identify_ingredients(req.image_base64)
    trace.end_span(span, metadata={"ingredients": ingredients_text})

    span = trace.start_span("search_by_ingredients")
    hits = hybrid_search(ingredients_text, collection)
    trace.end_span(span, metadata={"count": len(hits)})

    if req.dietary_filter:
        hits = [
            h for h in hits
            if req.dietary_filter.lower() in h.get("metadata", {}).get("dietary", "").lower()
        ]

    hits = rerank(ingredients_text, hits)
    results = format_results(hits)

    return {
        "identified_ingredients": ingredients_text,
        "results": results,
        "trace": trace.summary(),
    }


@app.get("/api/recipe/{recipe_id}")
async def get_recipe(recipe_id: str):
    for recipe in recipes:
        if recipe["id"] == recipe_id:
            safe_recipe = recipe.copy()
            if "description" in safe_recipe:
                safe_recipe["description"] = redact_pii(safe_recipe["description"])
            return safe_recipe
    raise HTTPException(status_code=404, detail="Recipe not found")
