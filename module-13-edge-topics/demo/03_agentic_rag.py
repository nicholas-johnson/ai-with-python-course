"""Part 3: The model decides what to search for."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")

DOCUMENTS = [
    {"id": "doc1", "text": "The reactor core operates at 5000K. Cooling uses liquid helium."},
    {"id": "doc2", "text": "Hull integrity on deck 5 is 94% after a micrometeorite impact."},
    {"id": "doc3", "text": "Navigation was serviced on stardate 4520. Star charts are current."},
    {"id": "doc4", "text": "The crew is 42: 12 officers, 20 enlisted, 10 civilian scientists."},
    {"id": "doc5", "text": "Protocol FTL-4092: shut down the reactor if the core exceeds 6000K."},
    {"id": "doc6", "text": "Fuel reserves are at 73%. Resupply at Station Omega in 14 days."},
    {"id": "doc7", "text": "The ship's AI answers crew queries with retrieval."},
    {"id": "doc8", "text": "Deck 7 is sealed after a coolant leak. Repair ETA is 6 hours."},
]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def demo_agentic_rag():
    print("=" * 60)
    print("PART 3: AGENTIC RAG")
    print("=" * 60)
    print()

    client = OpenAI()

    def search_fn(query: str) -> list[dict]:
        query_emb = client.embeddings.create(
            model="text-embedding-3-small", input=query
        ).data[0].embedding
        scored = []
        for doc in DOCUMENTS:
            emb = client.embeddings.create(
                model="text-embedding-3-small", input=doc["text"]
            ).data[0].embedding
            sim = cosine_similarity(query_emb, emb)
            scored.append({"id": doc["id"], "text": doc["text"], "score": round(sim, 3)})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:3]

    tools = [{
        "type": "function",
        "name": "search_documents",
        "description": "Search ship documents for relevant information.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query."}},
            "required": ["query"],
        },
    }]

    question = (
        "What is the reactor temperature and is there an emergency protocol if it gets too hot?"
    )
    print(f"Question: '{question}'\n")

    messages = [
        {
            "role": "system",
            "content": "Answer questions about the ship using the search tool when needed.",
        },
        {"role": "user", "content": question},
    ]

    for _ in range(3):
        response = client.responses.create(
            model=MODEL, reasoning={"effort": "none"}, input=messages, tools=tools
        )
        calls = [item for item in response.output if item.type == "function_call"]
        if calls:
            messages += response.output
            for tc in calls:
                args = json.loads(tc.arguments)
                print(f"  Agent searches: '{args['query']}'")
                results = search_fn(args["query"])
                for hit in results[:2]:
                    print(f"     → [{hit['id']}] (score={hit['score']}) {hit['text'][:50]}...")
                messages.append({
                    "type": "function_call_output",
                    "call_id": tc.call_id,
                    "output": json.dumps(results),
                })
            print()
        else:
            print(f"Agent's answer:\n  {response.output_text}\n")
            break
