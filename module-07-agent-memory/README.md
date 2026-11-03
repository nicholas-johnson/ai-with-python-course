# Module 7 — Agent Memory and Context Engineering

> An LLM has no memory between API calls. Every request is stateless — the model sees only the tokens you send. "Memory" is therefore a design pattern with two halves: you **write** things to a store outside the model, and you **select** the relevant ones back into the next prompt. Everything in this module is a move against a single budget: the context window.

## Learning goals

- Account for a context window as a **budget** and know where the tokens actually go.
- **Write** memories worth keeping, and **supersede** facts instead of stacking contradictions.
- **Select** memories by semantic recall, scored on relevance, recency, and importance.
- **Compact** a long conversation without losing the decisions and open tasks inside it.
- Expose memory and compaction as **MCP tools** so any agent can use them.

---

## The context budget

Every call you make sends the whole prompt again, and every token in it costs money, adds latency, and competes for the model's attention. A chat agent's prompt is rarely mostly conversation:

| Component | Typical share of a working agent prompt |
| --------- | --------------------------------------- |
| System prompt and persona | small, fixed |
| Tool schemas | grows with every tool you register |
| Retrieved documents | the biggest single consumer in a RAG agent |
| Conversation history | grows every single turn, forever |
| Injected memories | small, if you select well |

Count it rather than guess. `tiktoken` gives exact numbers for the `o200k_base` encoding used by current OpenAI models (Module 4 introduced this):

```python
import tiktoken

enc = tiktoken.get_encoding("o200k_base")

def count_tokens(messages: list[dict]) -> int:
    """Approximate the prompt cost of a message list."""
    return sum(len(enc.encode(str(m.get("content", "")))) + 4 for m in messages)
```

A bigger window is not a licence to fill it. Model accuracy degrades as the window fills — distractors crowd out the relevant tokens, and material in the middle of a long prompt gets less attention than material at either end. This is often called **context rot**. The practical consequence: a tightly selected 2,000-token prompt usually beats a sprawling 100,000-token one, and it is twenty times cheaper.

So context engineering has three moves, and the rest of this module is one section per move:

- **Write** — put durable things in a store outside the prompt.
- **Select** — pull back only what this turn needs.
- **Compress** — when history still will not fit, compact it rather than truncate it.

---

## Write: what is worth remembering

Most of what a user says is not memory-worthy. A good filter asks whether the fact will still matter next week:

| Worth writing | Not worth writing |
| ------------- | ----------------- |
| Preferences — "I always take the Comet Tail with extra fizz" | One-off questions — "what's on tap tonight?" |
| Constraints — "I'm allergic to synthcitrus" | Transient state — "I'm waiting on my crewmate" |
| Identity — "I'm the quartermaster on the Pathfinder" | Chitchat and pleasantries |
| Commitments — "Marek owes 12 credits on his tab" | Anything already in your database |

Let the model make the call with a structured decision, so you get a typed answer instead of prose to parse:

```python
class MemoryKind(str, Enum):
    preference = "preference"
    constraint = "constraint"
    identity = "identity"
    commitment = "commitment"


class MemoryCandidate(BaseModel):
    text: str = Field(description="The fact, written as a standalone sentence")
    kind: MemoryKind
    importance: float = Field(ge=0.0, le=1.0)


class WriteDecision(BaseModel):
    candidates: list[MemoryCandidate]
```

Two places you can run this. On the **hot path**, right inside the turn, the memory is available immediately but the user waits for a second model call. In the **background**, after the response is streamed, the turn stays fast but the memory lands a beat later. Chat products generally write in the background; this module writes on the hot path so the effect is visible in the demo.

### Supersede, do not append

The failure that actually bites in production is contradiction. A patron says "keep it brief" in March and "give me the full detail" in June. Append both and the model now receives two opposing instructions and picks one at random, turn by turn.

The near-miss is duplication. "I always take the Comet Tail" said three times over three visits is three memories saying one thing, crowding out the facts that only got said once.

Both are resolved on write, and both need the same first step: recall the neighbours of the new fact, because a contradiction or a duplicate is always semantically close to it.

```python
class MergeDecision(BaseModel):
    action: Literal["store", "replace", "skip"]
    target: int = -1          # which existing memory, for replace and skip
    reason: str


neighbours = store.recall(candidate.text, patron=patron, k=3)
decision = resolve(candidate.text, neighbours, client)      # structured call

if decision.action == "skip":
    return                                                   # already held
memory_id = store.remember(candidate.text, patron=patron, kind=candidate.kind)
if decision.action == "replace":
    store.supersede(neighbours[decision.target].memory_id, by=memory_id)
```

`supersede` flips the old entry's `active` flag to `False` and records the id that replaced it. The entry stops being recalled, but the trail survives — which is also exactly what you want for a privacy request. `forget(memory_id)` is the same soft delete with no replacement: the content stops reaching the model, while the record that something was removed remains for audit.

---

## Select: semantic recall

Early memory systems key memories by topic and look them up by prefix — `recall("drink_")`. It fails the moment the words diverge, which is immediately: the patron asks "what do I usually drink?" and the memory is filed under `favourite_beverage`.

Recall is a retrieval problem, so use the retrieval tools from Module 5. Memories go into a vector collection, and the current turn is the query:

```python
collection = chromadb.PersistentClient(path=CHROMA_PATH).get_or_create_collection(
    "cantina_memories",
    embedding_function=None,                            # we embed ourselves
    configuration={"hnsw": {"space": "cosine"}},        # distance in [0, 2]
)

collection.add(
    ids=[memory_id],
    embeddings=[embed(text, client)],
    documents=[text],
    metadatas=[{"patron": patron, "kind": kind, "importance": importance,
                "written_at": time.time(), "active": True}],
)
```

The `patron` metadata field is not decoration. It is the namespace, and the `where` filter on every query is what stops one patron's memories leaking into another's prompt:

```python
results = collection.query(
    query_embeddings=[embed(query, client)],
    n_results=k * 4,                                    # over-fetch, then rescore
    where={"$and": [{"patron": {"$eq": patron}}, {"active": {"$eq": True}}]},
)
```

### Scoring: relevance, recency, importance

Similarity alone is not enough. A stale fact and a fresh one can read almost identically, and the fresh one should win. Over-fetch from the vector store, then rank on three signals:

```python
similarities = [1.0 - d for d in results["distances"][0]]   # cosine distance -> similarity
relevances = normalise(similarities)                        # spread across [0, 1]

for relevance, metadata in zip(relevances, metadatas):
    age_days = (time.time() - metadata["written_at"]) / 86_400
    recency = 0.5 ** (age_days / HALF_LIFE_DAYS)            # decay, as a weight
    score = 0.6 * relevance + 0.25 * recency + 0.15 * metadata["importance"]
```

That `normalise` step is not cosmetic. Cosine similarity between two short sentences lands in a narrow band — in the demo, the six memories score between 0.03 and 0.38 against any given query — while recency spans the full 0 to 1. Blend the raw numbers and recency decides every ranking. Min-max across the candidates you actually retrieved makes the weights mean what they say.

This is also where decay belongs. Treating decay as a garbage collector — multiply importance by 0.9 each tick, delete below a threshold — throws away facts that were merely quiet for a while, and an allergy does not become less true because nobody mentioned it. In the demo, a 210-day-old constraint has a recency weight of 0.008 and still ranks first when the patron asks for something citrus-forward, because relevance and importance carry it. As a half-life weight, decay does its real job: all else equal, prefer the recent fact, and let an old one resurface when it is the only thing that matches.

Then inject the top handful, not everything you hold:

```python
memories = store.recall(user_input, patron="zara", k=5)
block = "\n".join(f"- {m.text}" for m in memories)
```

---

## Compress: compaction, not truncation

Selection handles memory. History is the other half of the problem, and it grows without bound: left alone, turn 50 sends every word of turns 1 through 49.

Dropping the oldest messages is the obvious fix and the wrong one. The oldest turns are where the decisions were made. "Charge everything to the ship's account" was agreed on turn 3; truncate turn 3 and the agent starts asking for payment again.

**Compaction** replaces a span of history with a summary that deliberately preserves the load-bearing parts. Name them explicitly rather than hoping the summary keeps them:

```python
class Anchor(BaseModel):
    kind: Literal["decision", "open_task", "constraint"]
    text: str


class Compaction(BaseModel):
    summary: str = Field(description="What was discussed, in under 120 words")
    anchors: list[Anchor] = Field(description="Decisions, open tasks, and constraints")
```

A compaction pass then replaces the old span with a single block and keeps the recent turns verbatim:

```python
def compact(messages: list[dict], *, budget: int, keep_recent: int, client) -> list[dict]:
    if count_tokens(messages) <= budget:
        return messages

    system, rest = messages[0], messages[1:]
    split = safe_split(rest, len(rest) - keep_recent)    # never split a tool pair
    old, recent = rest[:split], rest[split:]

    result = summarise(old, client)                      # -> Compaction
    block = render_block(result)                         # summary + anchor bullets
    return [system, {"role": "system", "content": block}, *recent]
```

Three things go wrong here, and all three are worth knowing before you ship:

- **Orphaned tool pairs.** A `function_call` and its `function_call_output` must stay together or the API rejects the request. `safe_split` walks the boundary backwards until it is not between a call and its output.
- **A broken cache prefix.** Prompt caching keys on the longest identical prefix. Rewrite index 0 and you pay full price on every subsequent call, so leave the system prompt byte-identical and insert the compaction block after it.
- **Summary-of-summary drift.** Compact a compaction repeatedly and detail bleeds away a generation at a time. Keep the anchors as structured text and re-emit them verbatim at each pass, so decisions survive even when the prose does not.

---

## Memory as MCP tools

Memory is state with a small, stable interface, which makes it a natural service rather than a library. Wrap it in an MCP server and any agent — yours, someone else's, a desktop client — gets the same memory without importing your code:

```python
mcp = MCPServer("Cantina Memory")

@mcp.tool()
def remember(patron: str, text: str, kind: str = "preference") -> str:
    """Store a durable fact about a patron."""

@mcp.tool()
def recall(patron: str, query: str, k: int = 5) -> str:
    """Recall the memories most relevant to a query, scored and ranked."""

@mcp.tool()
def compact_thread(budget_tokens: int = 1200) -> str:
    """Compact the stored conversation to fit a budget, preserving anchors."""
```

Both halves of the module belong on that server. Memory tools let the agent write and select; compaction tools let it compress. The agent decides when to call them, and the store outlives any single agent process.

---

## Summary

- **Budget the window.** Count tokens, know which component is eating them, and remember that a full window reads worse than a selective one.
- **Supersede, do not append.** A new fact that contradicts an old one replaces it, and one that merely repeats it is skipped. Soft-delete keeps the audit trail without feeding the model the conflict.
- **Recall semantically and score it.** Embed memories, filter by namespace, then rank on relevance, recency, and importance. Decay is a weight, not a delete.
- **Compact, do not truncate.** Preserve decisions, open tasks, and constraints by name, keep tool pairs intact, and leave the cache prefix alone.

---

## Demos

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python module-07-agent-memory/demo/demo.py

# Option B - uv (no activation needed):
uv run python module-07-agent-memory/demo/demo.py
```

Menu:

1. Context budget — where the tokens go, and what truncation destroys
2. Semantic memory — vector recall with scoring, next to prefix matching
3. Memory writer — structured write decisions and supersession
4. Compaction — anchors preserved under a token budget
5. Memory agent — chat with semantic recall and auto-compaction

Parts 1 and 4 run without an API key (part 4 falls back to a stub summariser). Parts 2, 3, and 5 need `OPENAI_API_KEY`. The memory store needs the `rag` extra for ChromaDB, which Module 5 already installed.

## Exercises

The three exercises chain together. Each builds on the last; you can bring your own code forward or use the provided solution.

| Folder | Mission |
| ------ | ------- |
| [`exercises/01-memory-store`](exercises/01-memory-store/) | Semantic memory store — scored recall, namespacing, supersede and forget |
| [`exercises/02-compaction`](exercises/02-compaction/) | Budget-triggered compaction that preserves anchors and tool pairs |
| [`exercises/03-memory-server`](exercises/03-memory-server/) | Expose memory and compaction as an MCP server, connect an agent via stdio |

Run tests for this module:

```bash
# Option A - pip + venv (run from the repo root):
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pytest module-07-agent-memory/

# Option B - uv (no activation needed):
uv run --extra dev pytest module-07-agent-memory/
```

## Slides

From repo root: `pnpm slides:07`, or `cd module-07-agent-memory/slides && pnpm dev`.

## Reference

- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Lost in the Middle (Liu et al. 2023)](https://arxiv.org/abs/2307.03172) — accuracy drops for material in the middle of a long context
- [MemGPT (Packer et al. 2023)](https://arxiv.org/abs/2310.08560)
- [Generative Agents (Park et al. 2023)](https://arxiv.org/abs/2304.03442) — the relevance/recency/importance retrieval score
- [LangChain memory (short-term)](https://docs.langchain.com/oss/python/langchain/short-term-memory) and [long-term](https://docs.langchain.com/oss/python/langchain/long-term-memory)
- [OpenAI prompt caching](https://platform.openai.com/docs/guides/prompt-caching)
