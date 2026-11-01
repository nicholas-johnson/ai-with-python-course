"""FastAPI backend for AI Movie Night — mood-based recommendations + text-to-SQL."""

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

    # TODO: Load data and build indexes on startup
    # 1. Read movies.json from DATA_DIR
    # 2. If movies.db doesn't exist, call build_database()
    # 3. Build the ChromaDB index with rag.build_index()
    # 4. Print a startup message

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

    # TODO: Implement recommendation endpoint
    # 1. Check recommend_cache for a cached result — if found, return with cached=True
    # 2. Call rag.search_by_mood() with k=10, wrap in a trace span
    # 3. Call rag.rerank() with top_k=5, wrap in a trace span
    # 4. Build the response dict, store in cache, return with cached=False
    pass


@app.post("/api/query")
def query(req: QueryRequest):
    trace = TraceContext()

    # TODO: Implement text-to-SQL endpoint
    # 1. Check query_cache — return cached if found
    # 2. Get the DB schema (trace span)
    # 3. Generate SQL from the question (trace span)
    # 4. Execute safely (trace span) — catch ValueError→400, Exception→500
    # 5. Format chart data
    # 6. Build response with sql, rows, row_count, chart, question
    # 7. Store in cache, return with cached=False
    pass


@app.get("/api/movie/{movie_id}")
def get_movie(movie_id: int):
    # TODO: Look up movie by id in movies_data, raise 404 if not found
    pass


@app.get("/api/schema")
def get_schema():
    # TODO: Return the DB schema as {"schema": ...}, raise 503 if DB not built
    pass
