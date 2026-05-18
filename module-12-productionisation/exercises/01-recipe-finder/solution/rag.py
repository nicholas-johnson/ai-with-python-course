"""RAG pipeline — indexing, hybrid search, and reranking."""

import json
from collections import defaultdict

import chromadb
from openai import OpenAI

from .config import EMBEDDING_MODEL, OPENAI_MODEL

client = OpenAI()


def build_index(recipes: list[dict]) -> tuple[chromadb.Collection, chromadb.ClientAPI]:
    """Embed recipe text into a ChromaDB in-memory collection."""
    chroma = chromadb.Client()
    try:
        chroma.delete_collection("recipes")
    except ValueError:
        pass
    collection = chroma.create_collection("recipes")

    documents = []
    metadatas = []
    ids = []

    for recipe in recipes:
        text = f"{recipe['title']}. {recipe.get('description', '')} Ingredients: {', '.join(recipe.get('ingredients', []))}"
        documents.append(text)
        metadatas.append({
            "recipe_id": recipe["id"],
            "title": recipe["title"],
            "cuisine": recipe.get("cuisine", ""),
            "dietary": ", ".join(recipe.get("dietary", [])),
            "cook_time": recipe.get("cook_time", ""),
        })
        ids.append(recipe["id"])

    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]

        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch_docs)
        embeddings = [item.embedding for item in response.data]

        collection.add(
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=batch_meta,
            ids=batch_ids,
        )

    return collection, chroma


def _bm25_search(query: str, collection: chromadb.Collection, k: int = 10) -> list[dict]:
    """Simple keyword search using ChromaDB's built-in document search."""
    all_data = collection.get(include=["documents", "metadatas"])
    query_terms = set(query.lower().split())

    scored = []
    for i, doc in enumerate(all_data["documents"]):
        doc_lower = doc.lower()
        score = sum(1 for term in query_terms if term in doc_lower)
        if score > 0:
            scored.append({
                "id": all_data["ids"][i],
                "document": doc,
                "metadata": all_data["metadatas"][i],
                "score": score,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def _vector_search(query: str, collection: chromadb.Collection, k: int = 10) -> list[dict]:
    """Semantic search using vector embeddings."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    query_embedding = response.data[0].embedding

    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return hits


def hybrid_search(query: str, collection: chromadb.Collection, k: int = 10) -> list[dict]:
    """Combine BM25 keyword search and vector search using Reciprocal Rank Fusion."""
    keyword_results = _bm25_search(query, collection, k=k)
    vector_results = _vector_search(query, collection, k=k)

    rrf_scores: dict[str, float] = defaultdict(float)
    doc_map: dict[str, dict] = {}
    rrf_k = 60

    for rank, hit in enumerate(keyword_results):
        rrf_scores[hit["id"]] += 1.0 / (rrf_k + rank + 1)
        doc_map[hit["id"]] = hit

    for rank, hit in enumerate(vector_results):
        rrf_scores[hit["id"]] += 1.0 / (rrf_k + rank + 1)
        doc_map[hit["id"]] = hit

    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)

    results = []
    for doc_id in sorted_ids[:k]:
        entry = doc_map[doc_id].copy()
        entry["rrf_score"] = rrf_scores[doc_id]
        results.append(entry)
    return results


def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Use the LLM to rerank search results by relevance."""
    if not results:
        return []

    candidates = "\n".join(
        f"{i+1}. [{r['metadata'].get('title', r['id'])}] {r['document'][:150]}"
        for i, r in enumerate(results[:10])
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a recipe relevance ranker. Given a query and candidate recipes, "
                    "return the numbers of the most relevant recipes in order of relevance. "
                    "Return ONLY a JSON array of numbers, e.g. [3, 1, 5]."
                ),
            },
            {
                "role": "user",
                "content": f"Query: {query}\n\nCandidates:\n{candidates}",
            },
        ],
        max_tokens=100,
    )

    try:
        raw = (response.choices[0].message.content or "").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        ranking = json.loads(raw)
        reranked = []
        for idx in ranking[:top_k]:
            if 1 <= idx <= len(results):
                reranked.append(results[idx - 1])
        return reranked if reranked else results[:top_k]
    except (json.JSONDecodeError, TypeError):
        return results[:top_k]


def format_results(hits: list[dict]) -> list[dict]:
    """Format search hits for the API response."""
    formatted = []
    for hit in hits:
        meta = hit.get("metadata", {})
        formatted.append({
            "id": meta.get("recipe_id", hit.get("id", "")),
            "title": meta.get("title", ""),
            "cuisine": meta.get("cuisine", ""),
            "dietary": meta.get("dietary", ""),
            "cook_time": meta.get("cook_time", ""),
            "score": round(hit.get("rrf_score", 1.0 - hit.get("distance", 0)), 4),
        })
    return formatted
