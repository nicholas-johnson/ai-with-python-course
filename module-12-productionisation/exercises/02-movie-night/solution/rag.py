"""RAG pipeline — embed movie plots into ChromaDB and search by mood."""

import chromadb
from openai import OpenAI
from .config import OPENAI_MODEL, EMBEDDING_MODEL

client = OpenAI()


def build_index(movies: list[dict]) -> chromadb.Collection:
    """Embed plot summaries into an in-memory ChromaDB collection."""
    chroma = chromadb.Client()

    try:
        chroma.delete_collection("movies")
    except Exception:
        pass

    collection = chroma.create_collection(
        name="movies",
        metadata={"hnsw:space": "cosine"},
    )

    ids, documents, metadatas = [], [], []
    for m in movies:
        text = f"{m['title']} ({m['year']}). {m['plot']}"
        ids.append(str(m["id"]))
        documents.append(text)
        metadatas.append({
            "title": m["title"],
            "year": m["year"],
            "director": m["director"],
            "rating": m["rating"],
            "genres": ", ".join(m.get("genres", [])),
        })

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_end = i + batch_size
        embeddings = _get_embeddings(documents[i:batch_end])
        collection.add(
            ids=ids[i:batch_end],
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end],
            embeddings=embeddings,
        )

    return collection


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def search_by_mood(query: str, collection: chromadb.Collection, k: int = 10) -> list[dict]:
    """Semantic search for movies matching a mood/description query."""
    query_embedding = _get_embeddings([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    matches = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        matches.append({
            "id": int(results["ids"][0][i]),
            "title": meta["title"],
            "year": meta["year"],
            "director": meta["director"],
            "rating": meta["rating"],
            "genres": meta["genres"],
            "score": round(1 - results["distances"][0][i], 3),
            "summary": doc,
        })

    return matches


def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Use the LLM to rerank search results by relevance to the query."""
    if not results:
        return []

    movie_list = "\n".join(
        f"{i+1}. {r['title']} ({r['year']}) — {r['summary'][:120]}"
        for i, r in enumerate(results)
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a movie recommendation assistant. "
             "Given a user's mood/request and a list of candidate movies, return ONLY "
             "the numbers of the most relevant movies in order of relevance, "
             "comma-separated. Example: 3,1,5"},
            {"role": "user", "content": f"Request: {query}\n\nCandidates:\n{movie_list}\n\n"
             f"Return the top {top_k} most relevant movie numbers:"},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    try:
        indices = [int(x.strip()) - 1 for x in raw.split(",")]
        reranked = [results[i] for i in indices if 0 <= i < len(results)]
        return reranked[:top_k]
    except (ValueError, IndexError):
        return results[:top_k]
