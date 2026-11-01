"""FastAPI backend for AI Movie Night — mood-based recommendations + text-to-SQL."""

import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import DATA_DIR, DB_PATH
from .tracing import TraceContext
from .cache import SemanticCache
from .build_db import build_database
from . import rag, sql

movies_data: list[dict] = []
collection = None
recommend_cache = SemanticCache(similarity_threshold=0.90, ttl_seconds=600)
query_cache = SemanticCache(similarity_threshold=0.95, ttl_seconds=600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global movies_data, collection

    movies_path = os.path.join(DATA_DIR, "movies.json")
    with open(movies_path) as f:
        movies_data = json.load(f)

    if not os.path.exists(DB_PATH):
        build_database()

    collection = rag.build_index(movies_data)
    print(f"Loaded {len(movies_data)} movies, index ready")

    yield


app = FastAPI(title="AI Movie Night", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    query: str


class QueryRequest(BaseModel):
    question: str


@app.get("/api/health")
def health():
    return {"status": "ok", "movies_loaded": len(movies_data)}


@app.post("/api/recommend")
def recommend(req: RecommendRequest):
    trace = TraceContext()

    cached = recommend_cache.get(req.query)
    if cached:
        return {**cached, "cached": True, "trace": trace.summary()}

    span = trace.start_span("search_by_mood")
    results = rag.search_by_mood(req.query, collection, k=10)
    trace.end_span(span, metadata={"candidates": len(results)})

    span = trace.start_span("rerank")
    top = rag.rerank(req.query, results, top_k=5)
    trace.end_span(span, metadata={"returned": len(top)})

    response = {"movies": top, "query": req.query}
    recommend_cache.set(req.query, response)
    return {**response, "cached": False, "trace": trace.summary()}


@app.post("/api/query")
def query(req: QueryRequest):
    trace = TraceContext()

    cached = query_cache.get(req.question)
    if cached:
        return {**cached, "cached": True, "trace": trace.summary()}

    span = trace.start_span("get_schema")
    schema = sql.get_schema(DB_PATH)
    trace.end_span(span)

    span = trace.start_span("text_to_sql")
    generated_sql = sql.text_to_sql(req.question, schema)
    trace.end_span(span, metadata={"sql": generated_sql})

    span = trace.start_span("execute_sql")
    try:
        rows = sql.safe_execute(DB_PATH, generated_sql)
    except ValueError as e:
        trace.end_span(span, status="error")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        trace.end_span(span, status="error")
        raise HTTPException(status_code=500, detail=f"SQL error: {e}")
    trace.end_span(span, metadata={"row_count": len(rows)})

    chart = sql.format_chart_data(rows, req.question)

    response = {
        "sql": generated_sql,
        "rows": rows,
        "row_count": len(rows),
        "chart": chart,
        "question": req.question,
    }
    query_cache.set(req.question, response)
    return {**response, "cached": False, "trace": trace.summary()}


@app.get("/api/movie/{movie_id}")
def get_movie(movie_id: int):
    for m in movies_data:
        if m["id"] == movie_id:
            return m
    raise HTTPException(status_code=404, detail="Movie not found")


@app.get("/api/schema")
def get_schema():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=503, detail="Database not built yet")
    return {"schema": sql.get_schema(DB_PATH)}
