# Module 7 — Instructor Notes

Delivery notes for Agent Memory and Context Engineering, the third Day 2 module. The course-wide [`instructor.md`](../instructor.md) has the one-page summary — note that its Module 7 entry is out of date and still describes the old decay-and-summarise version. This file is the detail: what the module covers, what to say, and what each demo is actually demonstrating.

---

## What this module covers

One budget, three moves against it, then the whole thing behind a service boundary:

1. **The context budget** — where the tokens actually go, and why a bigger window is not a licence to fill it.
2. **Write** — what is worth keeping, and what a new fact does to the old one it contradicts.
3. **Select** — recall as a retrieval problem, scored on relevance, recency, and importance.
4. **Compress** — compaction rather than truncation, with the decisions named so they survive.
5. **Memory as MCP tools** — memory is state behind a small interface, so it is a service, not a library.

### What it deliberately does not cover

- **Retrieval itself.** Embeddings, vector stores and the `where` filter are Module 5's material being reused. Say that out loud at the top of the Select section — "you already know how to do this, the new part is what goes in the store and who writes it."
- **Frameworks.** LangChain's short-term and long-term memory abstractions are Module 10. This module builds the thing those wrap. The reference links at the bottom of the README are the ones to point at if someone asks early.
- **Shared memory between agents.** Module 9. The MCP server at the end of this module makes it look adjacent, and it is, but a second agent reading the same store raises write-conflict questions this module does not answer.
- **Agent control flow.** The Part 5 chat loop is deliberately a plain loop. Module 8 is the one about who owns the control flow.

### The gap in the slide deck — read this before you present

A substantial chunk of the Write section is **commented out** in `slides/src/slides.js`: the typed write decision, hot path versus background, "supersede, do not append", and the `resolve`-on-write code slide. The "decay is a weight, not a delete" slide in the Select section is commented out too.

That matters because supersession is **the thing demo 3 exists to show** and the thing exercise 01's `write_memories` is built around. As the deck currently stands, the Write section is three slides (worth writing, not worth writing, done) and then a demo pointer that covers Parts 2 *and* 3 — so the writer demo runs with nothing behind it.

Two options, and you need to pick one before you walk in:

- **Uncomment them.** They are complete and in the right order; the comment markers are the only thing wrong with them. This is the better option if you have the time in the deck.
- **Teach supersession off the demo.** Run Part 3 and narrate the three outcomes from its printed output, which spells them out. Works fine, but you are asking the room to follow an argument with no slide to look at, so slow down for it.

Either way, do not let the module reach the Compress section without having made the supersede argument. It is the part delegates will actually hit in production.

---

## The spine

Two sentences, and everything else hangs off them:

> The model is stateless. Every call resends the whole prompt, so "memory" is not something the model has — it is something you build: you **write** facts to a store outside the model, and you **select** them back in.

> Every component of the prompt is resent every turn, and exactly one of them grows without limit: history.

Things worth saying out loud:

- **"A tight 2k prompt beats a sprawling 100k one, and costs two percent as much."** This is the line that lands with people who arrived thinking the long-context models solved this. Context rot is the mechanism — accuracy degrades as the window fills, and material in the middle gets the least attention.
- **Memory is the cheapest component and the highest leverage.** Five well-chosen facts are about fifty tokens. That ratio is why selection is worth doing properly.
- **Both halves of the problem are budget problems.** Memory handles durable facts; compaction handles history. Delegates who see them as two unrelated features lose the thread at the Compress section.

Expect pushback of the form "why bother, windows are huge now." The counter is not capability — it is that a full window reads *worse* than a selective one, and costs fifty times more to read badly.

---

## Talk track, section by section

Slide numbers below refer to the **live** deck — the uncommented slides, 29 of them. If you uncomment the Write section the later numbers shift.

### 1. The context budget (slides 4–8)

Open on the cards slide: system and tools, retrieved docs, history, memories. Then land the one asymmetry that matters — three of those four have a ceiling, and history does not.

The tool schemas card is worth a beat. Delegates generally do not think of tool definitions as prompt cost, and "twenty tools can outweigh the conversation" is a genuinely new idea for most rooms. It also connects backwards: every tool they registered in Modules 2 and 3 is being resent on every call.

Then context rot, then `count_tokens`. The point of the code slide is small: **measure each component separately**, because you cannot budget what you cannot see.

### 2. Write (slides 9–11, plus whatever you restore)

The filter question is the whole section: **will this still matter next week?** Preferences, constraints, identity, commitments pass. Questions, transient state and chitchat do not.

The one line delegates most need: **"anything already in your database — look it up, do not remember it."** Memory is for things the conversation produced, not for a cache of your own data.

Then supersession, from slides or from the demo. The argument in order:

- The failure that actually bites is **contradiction**. "Keep it brief" in March, "give me the full detail" in June. Append both and the prompt now carries two opposing instructions, and the model picks one at random, turn by turn. The agent does not look broken in an obvious way — it looks inconsistent, which is worse to debug.
- The near miss is **duplication**. The same preference said on three visits is three memories crowding out facts that were only said once.
- Both are resolved **on write**, while you still know which is newer. Both need the same first step: recall the neighbours, because a contradiction or a duplicate is always semantically close to the new fact.
- `supersede` is a soft delete that records what replaced it. `forget` is the same soft delete with no replacement — the content stops reaching the model, the record that something was removed survives for audit.

If you have time for one aside, make it hot path versus background: the demo writes inside the turn so the effect is visible, chat products write after the response streams so the turn stays fast.

### 3. Select (slides 12–15)

Lead with keyed lookup failing, because it is concrete: the patron asks "what do I usually drink?", the memory is filed under `favourite_beverage`, nothing matches. Then: recall is retrieval, and you already have the tools.

Two engineering points not to skip:

- **`patron` is the namespace, not decoration.** The `where` filter on every query is the only thing standing between the demo and a privacy incident. Say it in those terms — one patron's memories appearing in another's prompt is the kind of bug that makes the news.
- **Normalise before you blend.** Raw cosine similarity between two short sentences sits in a narrow band — 0.03 to 0.38 in this demo — while recency spans the full 0 to 1. Blend them raw and recency decides every ranking, silently. Min-max across the candidates you actually retrieved is what makes the weights mean what they say.

The decay argument, whether or not you restore its slide: treating decay as a garbage collector throws away facts that were merely quiet. An allergy does not become less true because nobody mentioned it. As a half-life *weight*, decay does its real job — prefer the recent fact all else equal, and let an old one resurface when it is the only thing that matches. Demo 2 proves this with a 210-day-old constraint that still ranks first.

### 4. Compress (slides 17–22)

The framing: selection handles memory, and history is the other half. Turn 50 resends turns 1 through 49.

Truncation is the obvious fix and the wrong one, for a specific reason worth stating precisely: **the oldest turns are where the decisions were made.** "Charge everything to the ship's account" was agreed on turn 3. That is the single example the whole module reuses, and it is in demos 1 and 4 both.

Then the structural move: do not hope the summary keeps the important parts, **name them**. Decisions, open tasks, constraints. Anchors are a Pydantic schema, so they can be re-emitted verbatim next pass.

The three failure modes slide is the most practically useful in the module:

- **Orphaned tool pairs** — a `function_call` without its output is an API error, not a degradation. `safe_split` walks the boundary back.
- **A broken cache prefix** — prompt caching keys on the longest identical prefix. Rewrite index 0 and you pay full price on every later call, which is a cost regression nobody will attribute to the compaction code that caused it.
- **Summary-of-summary drift** — compact a compaction repeatedly and detail bleeds away a generation at a time. Carried anchors re-emitted verbatim are the defence.

### 5. Memory as a service (slides 23–25)

Short section. The claim: memory is state behind a small, stable interface, which is the definition of a service. Put it behind MCP and any agent — yours, someone else's, a desktop client — gets the same memory with no imports.

The point worth making that the slide does not: **both halves belong on the server.** Memory tools the model calls when it wants to; compaction tools the *harness* calls because the thread has to be recorded whatever the model decides. That split is exactly what exercise 03 is about, and flagging it here saves confusion later.

---

## The demos

Run via the menu: `python module-07-agent-memory/demo/demo.py`. Each part also runs standalone, e.g. `python module-07-agent-memory/demo/02_semantic_memory.py`.

**Parts 1 and 4 need no API key** — part 4 falls back to a stub summariser and says so. Parts 2, 3 and 5 need `OPENAI_API_KEY` and ChromaDB from Module 5's `rag` extra.

The demo store is an **ephemeral** Chroma client, so the demos leave nothing on disk and every run starts clean. The exercises are the opposite — see below.

### 01 — The context budget

No model call, instant, offline. Prints the five components of one turn with proportional bars, then truncates the thread to a 540-token budget.

```
  One turn of a working agent — 1078 tokens:

    System prompt       89  ##............................    8%
    Tool schemas       228  ######........................   21%
    Retrieved docs     201  ######........................   19%
    Memories            51  #.............................    5%
    History            509  ##############................   47%
```

**What to point at:** history at 47% on a *short* thread, and memories at 5%. Then the truncation result — 14 of 24 messages dropped, and the one it prints is the ship's account decision. The closing lines spell out the consequence: the agent now starts chasing the Pathfinder crew for credits individually, because as far as it can see nobody ever told it not to.

This is the demo that sets up Part 4, so say explicitly that you will compact the *same thread* later and compare.

### 02 — Semantic memory

Seeds six memories for one patron, aged 2 to 210 days, then runs three turns as retrieval queries and prints the score breakdown — score, relevance, recency, importance — for the top three each time.

**What to point at**, in this order:

- The **synthcitrus constraint** on the citrus query. It is 210 days old, its recency weight is 0.008, and it still comes first. Relevance and importance carry it. Decay-as-a-delete would have binned it, and the agent would have served an allergen.
- `prefix_recall("drink_")` returning **zero results** on a store that plainly holds the answer. The memory is filed under `favourite_beverage`. Semantic recall found it on the first query.
- The relevance column being normalised rather than raw. The demo prints the explanation; it is worth reading out, because this is the detail most likely to bite someone building their own.

### 03 — The memory writer

Six turns go to the writer: one-off questions, transient state, chitchat, a duplicate, a contradiction, and a genuinely new fact.

**What to point at:** most turns print `-> nothing durable here`. That is the correct answer and the one delegates least expect — they tend to assume a memory system writes something every turn.

Then the three outcomes, which the demo names explicitly at the end:

- **skip** — "the Comet Tail, extra fizz" is already held in the same detail.
- **replace** — "give me the full detail" cannot stand beside "prefers her briefings short". The old one goes `active=False` with the id that replaced it, so you can still answer what the agent believed and when.
- **store** — the quartermaster fact is new.

Close on the counterfactual: append everything instead and the prompt carries both briefing instructions at once.

**Variance warning:** this is a live model making judgement calls, so the exact outcomes can shift between runs. The skip and the replace are the robust ones; if a run surprises you, that is a discussion rather than a problem — ask the room whether the model's call was defensible.

### 04 — Compaction

Offline-capable and therefore the safest demo to run if the network is unreliable. With no key it uses a stub summariser with fixed anchors — say so, and do not claim the model produced them.

Three acts. First the split boundary:

```
  Wanted to split at index 18: function_call_output   {"drink": "Comet Tail", ...
  That is a tool output — its call sits at index 17.
  safe_split moved the boundary back to 17: function_call          {"drink": "Comet Tail"}
```

Then the compaction — 17 messages into one block, 876 tokens down to 521, three anchors preserved and printed. Then the same thread truncated to the same budget, listing what it lost, including the ship's account turn.

**What to point at:** both reached the budget; only one of them still knows what was agreed. That is the entire argument, and the side-by-side is what makes it stick.

**Two things that vary:** with a real API key the summary is genuinely generated, so the token count after compaction moves. If it lands above the budget the demo prints a note explaining that one pass gets you most of the way and a real agent rechecks and compacts again — that note is useful, not a failure. The stub path happens to land under budget, so you will not see it offline.

### 05 — Memory agent

The interactive one: all three moves in one chat loop. Every turn recalls the top five memories, compacts if the thread is over 900 tokens, answers, then writes anything durable. Three memories are seeded, including the synthcitrus constraint.

Commands: `/budget`, `/memories`, `/compact`, `/forget <n>`, `quit`.

**A sequence that works well in front of a room:**

1. Ask for something citrus-forward and watch the `[recalled: ...]` line show the constraint being pulled in, with its score.
2. `/budget` early, to see the breakdown while it is small.
3. Chat for a while — the budget is deliberately set low, so a normal conversation trips the auto-compaction and prints `[auto-compacted N messages, X -> Y tokens]`.
4. Tell it something durable and watch the writer fire inline.
5. `/forget` a memory, then ask about it again, and watch the agent no longer know.

The `/forget` beat is the one worth doing if you only do one — it makes the soft-delete argument concrete, and it is the natural place for the privacy conversation.

---

## Exercises

Three, chained. Delegates can carry their own code forward or use the provided solution — exercises 02 and 03 ship `memory_store.py` and `compaction.py` as completed versions of the earlier work.

| Folder | What they build | Where they get stuck |
| ------ | --------------- | -------------------- |
| `01-memory-store` | Scored semantic recall, namespacing, supersede and forget | Forgetting to normalise, which makes recency dominate and the ranking test fail. Chroma metadata rejecting `None`, which is why `superseded_by` starts as `""`. The `where` filter needs *both* clauses — patron and `active` — and the namespacing test catches only one of those mistakes. |
| `02-compaction` | Budget-triggered compaction preserving anchors and tool pairs | `count_tokens` missing `arguments` and `output`, so tool items count as free — exactly backwards. `safe_split` indexing at `len(messages)` and raising. And in `chat`, rebinding the local instead of `thread[:] = compacted`, so the caller keeps the old thread. |
| `03-memory-server` | Memory and compaction as MCP tools, agent connected over stdio | `thread_budget` must literally contain the word **"over"** — the client greps for it. `record_turns` has the same aliasing trap: `messages[:] = [messages[0], *thread]`, not a rebind. And the point everyone misses first time: after a compaction you have to rebuild the *model's* context from the server's thread, or the saving exists on the server and nowhere that matters. |

**Exercise 03's README is out of date.** It describes an earlier design — key/value `remember(key, value)`, a `get_summary` tool, a `summary.py` module, five tools total. The actual `server.py` has nine TODOs across two groups: `remember` / `recall` / `forget` / `list_memories` for memory, and `append_turn` / `thread_budget` / `compact_thread` / `get_thread` / `get_anchors` for compaction, plus a `merge_anchors` helper that is not a tool. **Tell delegates to follow the TODOs in the file, not the tool table in the README.** The architecture narrative at the top of that README is still accurate.

**The exercises use a persistent Chroma store**, at `chroma_data/` inside each exercise directory (gitignored). That is deliberate — memory outliving the process is the point — but it means a delegate who has been experimenting will carry stale memories into their next run. If someone reports recall returning facts they never mentioned this session, deleting `chroma_data/` is the fix. Worth mentioning once at the start of exercise 01 so nobody debugs it for ten minutes.

**Running tests:** per exercise, from inside its folder:

```bash
cd module-07-agent-memory/exercises/01-memory-store
pytest test_start.py -v
```

A bare `pytest module-07-agent-memory/` **cannot collect** — all three exercises have a `test_start.py` and there are no package markers, so pytest reports an import file mismatch. The module README currently suggests the bare form; it does not work. This is true across the whole course, not something specific to module 7.

Tests fail by design against the unimplemented `start.py` — 12, 15 and 15 failures respectively. That is the starting state, not a broken checkout. No test needs an API key or a real ChromaDB: exercise 01 uses a dict-backed collection stub with canned distances, and 02 and 03 mock `responses.parse`.

---

## Questions you should expect

**"Why bother, when the model has a million-token window?"**
Cost, latency, and accuracy — in that order of how convincing they are to engineers, and reverse order of how much they actually matter. A full window reads worse than a selective one. Point at context rot and the "lost in the middle" reference.

**"Isn't this just RAG?"**
Select is, exactly — same embeddings, same store, same filter. The difference is on the write side. RAG indexes documents you already have; memory writes facts the conversation produced, which means someone has to decide what is worth keeping and what a new fact does to an old one. Modules 5 and 7 share the retrieval half and differ entirely on the other.

**"Why not append everything and let the model work out the contradiction?"**
Because it cannot tell which is newer — nothing in the prompt says so — and it picks one at random each turn. The agent does not fail loudly, it just behaves inconsistently, which is far harder to diagnose.

**"Why let a model decide what to remember? Why not rules?"**
It is a model call, but a tightly constrained one: a typed schema, a fixed set of kinds, and a merge policy that lives in code. The model proposes; the code decides what happens to the store. Rules alone cannot tell "I'm allergic to synthcitrus" from "I don't fancy citrus tonight".

**"Is a soft delete good enough for a privacy request?"**
For "stop using this about me", yes — `forget` takes the content out of recall immediately, and the surviving row proves something was removed without retaining what it said. For a true erasure request you need a hard-delete path as well. Good discussion, and an honest "this demo shows one of the two" is the right answer.

**"Where do the 0.6 / 0.25 / 0.15 weights come from?"**
The Generative Agents paper, linked in the README. They are a reasonable starting point, not a law. Exercise 01's stretch goal is to push recency to 0.6 and find a query where the ranking becomes obviously wrong — that is a faster way to understand them than arguing about them.

**"Why compact rather than retrieve over the history?"**
You can do both, and production systems often do. The reason compaction exists alongside retrieval: decisions and constraints need to be *always present*, not retrieved when the topic happens to match. "Charge it to the ship's account" has to be in the prompt on the turn where nobody mentions payment.

**"Is this how ChatGPT's memory works?"**
Broadly, yes — write in the background, select into the prompt, with a user-visible list and a delete. Useful anchor for anyone who has seen it from the outside.

---

## Setup and prerequisites

- `OPENAI_API_KEY` for demo parts 2, 3 and 5, and for running any exercise interactively. Parts 1 and 4 and every test run without one.
- ChromaDB, from Module 5's `rag` extra. If Module 5 ran, this is already installed.
- Module 5 is a genuine prerequisite, not just a reference — embeddings, cosine distance, and `where` filters all come from it. If a group skipped it, budget a few minutes before the Select section.
- Slides: `pnpm slides:07` from the repo root, or `cd module-07-agent-memory/slides && pnpm dev`.
- Delete `exercises/*/chroma_data/` between delivery sessions if you are reusing a machine.
