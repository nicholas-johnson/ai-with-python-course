export const slides = [
  {
    type: 'title',
    content: {
      title: 'Module 7 — Agent Memory',
      subtitle: 'Context engineering: what to write, what to select, what to compress',
      icon: 'brain',
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'The model is stateless. Memory is something you build.',
      points: [
        'Every call sends the whole prompt again — the model remembers nothing on its own.',
        'Memory is two moves: **write** facts to a store, **select** them back into the prompt.',
        'Compaction is the third move, for when history still will not fit.',
        'All three are moves against one budget: the context window.',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Learning goals',
      icon: 'target',
      points: [
        'Account for the context window as a **budget** and see where tokens go.',
        '**Write** memories worth keeping, and **supersede** rather than stack contradictions.',
        '**Select** by semantic recall, scored on relevance, recency, and importance.',
        '**Compact** long conversations without losing decisions and open tasks.',
        'Expose memory and compaction as **MCP tools**.',
      ],
    },
  },

  // ---- Section: The context budget ----
  {
    type: 'title',
    content: {
      title: 'The context budget',
      subtitle: 'Keeping it under control',
      icon: 'scale',
    },
  },
  {
    type: 'cards',
    content: {
      title: 'Where Context actually goes',
      cards: [
        {
          heading: 'System + tools',
          points: [
            'Persona and policy — fixed cost',
            'Tool schemas grow with every tool you register',
            'Twenty tools can outweigh the conversation',
          ],
        },
        {
          heading: 'Retrieved docs',
          points: [
            'The biggest consumer in a RAG agent',
            'Chunk count times chunk size',
            'Reranking here buys budget everywhere else',
          ],
        },
        {
          heading: 'History',
          points: [
            'Grows every single turn, forever',
            'Turn 50 resends turns 1-49',
            'The only component with no natural ceiling',
          ],
        },
        {
          heading: 'Memories',
          points: [
            'Small — if you select well',
            'Five facts, not fifty',
            'Cheapest component, highest leverage',
          ],
        },
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Context rot',
      icon: 'alert-triangle',
      points: [
        'A bigger window is not a licence to fill it.',
        'Accuracy **degrades as the window fills** — distractors crowd out signal.',
        'Material in the **middle** of a long prompt gets the least attention.',
        'A tight 2k prompt beats a sprawling 100k one — and costs 2% as much.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Count, do not guess',
      code: `import tiktoken

enc = tiktoken.get_encoding("o200k_base")


def count_tokens(messages: list[dict]) -> int:
    """Approximate the prompt cost of a message list."""
    return sum(
        len(enc.encode(str(m.get("content", "")))) + 4
        for m in messages
    )`,
      highlights: [
        '`o200k_base` is the encoding for current OpenAI models (Module 4)',
        'Measure each component separately — you cannot budget what you cannot see',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — The context budget',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 1',
      icon: 'rocket',
    },
  },

  // ---- Section: Write ----
  {
    type: 'title',
    content: {
      title: 'Write',
      subtitle: 'What is worth keeping, and what to do when facts collide',
      icon: 'database',
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Worth writing: will it matter next week?',
      rules: [
        {
          rule: 'Preferences',
          example:
            '"I always take the Comet Tail with extra fizz" — shapes every future turn.',
          icon: 'star',
        },
        {
          rule: 'Constraints',
          example: '"I am allergic to synthcitrus" — never stops being true.',
          icon: 'ban',
        },
        {
          rule: 'Identity',
          example: '"I am the quartermaster on the Pathfinder" — who you are talking to.',
          icon: 'user',
        },
        {
          rule: 'Commitments',
          example: '"Marek owes 12 credits" — an open loop someone has to close.',
          icon: 'clipboard-list',
        },
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Not worth writing',
      icon: 'eraser',
      points: [
        'One-off questions — *"what is on tap tonight?"*',
        'Transient state — *"I am waiting on my crewmate"*',
        'Chitchat and pleasantries.',
        'Anything already in your database — **look it up, do not remember it**.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'A typed write decision',
      code: `class MemoryCandidate(BaseModel):
    text: str = Field(description="A standalone sentence")
    kind: Literal["preference", "constraint",
                  "identity", "commitment"]
    importance: float = Field(ge=0.0, le=1.0)


class WriteDecision(BaseModel):
    candidates: list[MemoryCandidate]


decision = client.responses.parse(
    model=MODEL, text_format=WriteDecision, input=[...]
).output_parsed`,
      highlights: [
        'Structured output means a typed answer, not prose to parse',
        'An empty candidate list is the common and correct case',
      ],
    },
  },
  {
    type: 'comparison',
    content: {
      title: 'Where the write happens',
      left: {
        label: 'Hot path',
        items: [
          'Extract inside the turn',
          'Memory available immediately',
          'User waits for a second model call',
          'What the demo does — visible effect',
        ],
      },
      right: {
        label: 'Background',
        items: [
          'Extract after the response streams',
          'Turn stays fast',
          'Memory lands a beat later',
          'What chat products ship',
        ],
      },
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Supersede, do not append',
      icon: 'arrow-up-down',
      points: [
        'In March: *"keep it brief."* In June: *"give me the full detail."*',
        'Append both and the model receives **two opposing instructions**.',
        'It picks one at random, turn by turn — and looks broken.',
        'Resolve the conflict **on write**, while you still know which is newer.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Resolve on write',
      code: `def write(self, text, *, patron, kind, importance=1.0):
    neighbours = self.recall(text, patron=patron, k=3)
    conflict = find_conflict(text, neighbours, self.client)

    memory_id = self.remember(
        text, patron=patron, kind=kind, importance=importance
    )
    if conflict:
        self.supersede(conflict.memory_id, by=memory_id)
    return memory_id`,
      highlights: [
        'Recall the neighbours first — a conflict is always semantically close',
        '`supersede` sets `active=False` and records what replaced it',
        '`forget(id)` is the same soft delete with no replacement: audit trail, no content',
      ],
    },
  },

  // ---- Section: Select ----
  {
    type: 'title',
    content: {
      title: 'Select',
      subtitle: 'Recall is a retrieval problem',
      icon: 'search',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Why keyed lookup fails',
      icon: 'frown',
      points: [
        'Early memory systems file by topic and look up by prefix: `recall("drink_")`.',
        'The patron asks *"what do I usually drink?"*',
        'The memory is filed under `favourite_beverage`. Nothing matches.',
        'You already have the fix from Module 5: **embed it and retrieve**.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Memories in a vector collection',
      code: `collection = chroma.get_or_create_collection(
    "cantina_memories",
    embedding_function=None,                   # we embed ourselves
    configuration={"hnsw": {"space": "cosine"}},
)

results = collection.query(
    query_embeddings=[embed(query, client)],
    n_results=k * 4,                           # over-fetch, then rescore
    where={"$and": [
        {"patron": {"$eq": patron}},
        {"active": {"$eq": True}},
    ]},
)`,
      highlights: [
        'The current turn is the query — no keys, no prefixes',
        '`patron` is the **namespace**: the `where` filter is what stops memory leaking between users',
        'Over-fetch from the index so there is something to rescore',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Score: relevance, recency, importance',
      code: `sims = [1.0 - d for d in distances]   # cosine -> similarity
rels = normalise(sims)               # spread across [0, 1]

for relevance, meta in zip(rels, metadatas):
    age_days = (now - meta["written_at"]) / 86_400
    recency = 0.5 ** (age_days / HALF_LIFE_DAYS)

    score = (0.6 * relevance
             + 0.25 * recency
             + 0.15 * meta["importance"])`,
      highlights: [
        'Similarity alone cannot tell a stale fact from a fresh one',
        '**Normalise first**: raw cosine spans 0.03-0.38 here, recency spans 0-1 — blend them raw and recency wins every time',
        'Inject the top five, not everything you hold',
      ],
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Decay is a weight, not a delete',
      icon: 'scale',
      points: [
        'The old way: multiply importance by 0.9 each tick, delete below a threshold.',
        'That discards facts that were merely **quiet for a while**.',
        'An allergy does not become less true because nobody mentioned it.',
        'As a **half-life weight** in the ranking: prefer the recent fact, all else equal.',
        'In the demo a 210-day-old constraint scores `recency = 0.008` — and still ranks first.',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — Semantic recall and the writer',
      subtitle: 'Switch to terminal: python demo/demo.py — Parts 2-3',
      icon: 'rocket',
    },
  },

  // ---- Section: Compress ----
  {
    type: 'title',
    content: {
      title: 'Compress',
      subtitle: 'Compaction, not truncation',
      icon: 'file-minus',
    },
  },
  {
    type: 'standard',
    content: {
      title: 'Truncation loses the decisions',
      icon: 'scissors',
      points: [
        'History is the one component with no ceiling — turn 50 resends turns 1-49.',
        'Dropping the oldest messages is the obvious fix and the wrong one.',
        'The oldest turns are **where the decisions were made**.',
        '*"Charge it to the ship\'s account"* was agreed on turn 3.',
        'Truncate turn 3 and the agent starts asking for payment again.',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'Name what must survive',
      code: `class Anchor(BaseModel):
    kind: Literal["decision", "open_task", "constraint"]
    text: str


class Compaction(BaseModel):
    summary: str = Field(
        description="What was discussed, under 120 words"
    )
    anchors: list[Anchor] = Field(
        description="Decisions, open tasks, and constraints"
    )`,
      highlights: [
        'Do not hope the summary keeps the important parts — extract them by name',
        'Anchors are structured, so they can be re-emitted verbatim next time',
      ],
    },
  },
  {
    type: 'code',
    content: {
      title: 'The compaction pass',
      code: `def compact(messages, *, budget, keep_recent, client):
    if count_tokens(messages) <= budget:
        return messages

    system, rest = messages[0], messages[1:]
    split = safe_split(rest, len(rest) - keep_recent)
    old, recent = rest[:split], rest[split:]

    result = summarise(old, client)        # -> Compaction
    block = render_block(result)           # summary + anchors
    return [system, {"role": "system", "content": block},
            *recent]`,
      highlights: [
        'Budget-triggered: no model call until you are actually over',
        'Recent turns stay verbatim; the old span becomes one block',
      ],
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Three ways compaction breaks',
      rules: [
        {
          rule: 'Orphaned tool pairs',
          example:
            'A `function_call` without its output is an API error. `safe_split` walks the boundary back until it is not between a call and its result.',
          icon: 'plug',
        },
        {
          rule: 'A broken cache prefix',
          example:
            'Prompt caching keys on the longest identical prefix. Leave index 0 byte-identical and insert the block after it.',
          icon: 'timer',
        },
        {
          rule: 'Summary-of-summary drift',
          example:
            'Compact a compaction repeatedly and detail bleeds away. Re-emit the anchors verbatim at every pass.',
          icon: 'refresh-cw',
        },
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — Compaction',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 4',
      icon: 'rocket',
    },
  },

  // ---- Section: Memory as a service ----
  {
    type: 'title',
    content: {
      title: 'Memory as a service',
      subtitle: 'Both halves, behind MCP',
      icon: 'plug',
    },
  },
  {
    type: 'code',
    content: {
      title: 'Memory and compaction as MCP tools',
      code: `mcp = MCPServer("Cantina Memory")


@mcp.tool()
def remember(patron: str, text: str, kind: str) -> str:
    """Store a durable fact about a patron."""


@mcp.tool()
def recall(patron: str, query: str, k: int = 5) -> str:
    """Recall the memories most relevant to a query."""


@mcp.tool()
def compact_thread(budget_tokens: int = 1200) -> str:
    """Compact the thread, preserving anchors."""`,
      highlights: [
        'Memory is state behind a small, stable interface — a service, not a library',
        'Any agent connects over stdio and gets the same memory, no imports',
        'The store outlives any single agent process',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Demo — Memory agent',
      subtitle: 'Switch to terminal: python demo/demo.py — Part 5',
      icon: 'rocket',
    },
  },

  // ---- Section: Wrap-up ----
  {
    type: 'title',
    content: {
      title: 'Putting it all together',
      subtitle: 'Summary and exercises',
      icon: 'check-square',
    },
  },
  {
    type: 'rules',
    content: {
      title: 'Summary',
      rules: [
        {
          rule: 'Budget the window',
          example:
            'Count the tokens, know which component is eating them. A full window reads worse than a selective one.',
          icon: 'scale',
        },
        {
          rule: 'Supersede, do not append',
          example:
            'A new fact that contradicts an old one replaces it. Soft-delete keeps the audit trail, not the conflict.',
          icon: 'arrow-up-down',
        },
        {
          rule: 'Recall semantically, then score',
          example:
            'Embed, filter by namespace, rank on relevance, recency, and importance. Decay is a weight, not a delete.',
          icon: 'search',
        },
        {
          rule: 'Compact, do not truncate',
          example:
            'Preserve decisions, open tasks, and constraints by name. Keep tool pairs intact and the cache prefix alone.',
          icon: 'file-minus',
        },
      ],
    },
  },
  {
    type: 'welcome',
    content: {
      title: 'Exercises',
      points: [
        '01 — Memory store: semantic recall with scoring, namespacing, supersede and forget',
        '02 — Compaction: budget-triggered compaction that preserves anchors and tool pairs',
        '03 — Memory MCP server: memory and compaction as tools, agent connected via stdio',
      ],
    },
  },
  {
    type: 'title',
    content: {
      title: 'Module 7 — Complete',
      subtitle: 'Next: structured workflows',
      icon: 'check-circle',
    },
  },
];
