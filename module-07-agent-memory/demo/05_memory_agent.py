"""Part 5: A chat that recalls semantically, writes as you talk, and compacts itself.
Needs OPENAI_API_KEY and the rag extra for ChromaDB.
Run alone:  python module-07-agent-memory/demo/05_memory_agent.py
"""

import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from budget import count_messages, count_text
from compaction import compact
from memory_store import MemoryStore
from memory_writer import write_turn
from sample_prompt import SYSTEM_PROMPT

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
PATRON = "zara"

# Small on purpose: a 20-turn evening will trip it, which is the point.
BUDGET_TOKENS = 900
KEEP_RECENT = 6
RECALL_K = 5

DAY = 86_400

SEED = [
    ("Zara takes the Comet Tail with extra fizz.", "preference", 0.9, 40),
    ("Zara is the quartermaster on the Pathfinder.", "identity", 0.8, 120),
    ("Zara reacts badly to synthcitrus in any form.", "constraint", 1.0, 210),
]


def build_prompt(thread: list[dict], memories: list) -> list[dict]:
    """Assemble the call: system prompt, recalled memories, then the thread."""
    if memories:
        block = "\n".join(f"- {m.text}" for m in memories)
        memory_message = {"role": "system", "content": f"What you remember about this patron:\n{block}"}
    else:
        memory_message = {"role": "system", "content": "You have no memories of this patron yet."}
    return [SYSTEM_PROMPT, memory_message, *thread]


def print_budget(thread: list[dict], memories: list):
    prompt = build_prompt(thread, memories)
    print(f"    system prompt   {count_text(SYSTEM_PROMPT['content']):>5}")
    print(f"    memories ({len(memories)})   {count_text(str(prompt[1]['content'])):>5}")
    print(f"    thread ({len(thread):>2})      {count_messages(thread):>5}")
    print(f"    total           {count_messages(prompt):>5}  / budget {BUDGET_TOKENS}")


def demo_memory_agent(client: OpenAI | None = None):
    client = client or OpenAI()

    print("=" * 60)
    print("PART 5: MEMORY AGENT")
    print("=" * 60)
    print()

    store = MemoryStore(client)
    now = time.time()
    for text, kind, importance, age_days in SEED:
        store.remember(
            text, patron=PATRON, kind=kind, importance=importance, written_at=now - age_days * DAY
        )

    print(f"  Seeded {len(SEED)} memories for '{PATRON}'. Every turn:")
    print(f"    1. recall the top {RECALL_K} memories for what you just said")
    print(f"    2. compact the thread if it is over {BUDGET_TOKENS} tokens")
    print("    3. answer, then write anything durable from your message")
    print()
    print("  Commands: /budget, /memories, /compact, /forget <n>, quit\n")

    thread: list[dict] = []
    carried: list = []
    memories: list = []

    while True:
        try:
            user_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input or user_input.lower() == "quit":
            break

        if user_input == "/budget":
            print_budget(thread, memories)
            print()
            continue

        if user_input == "/memories":
            rows = store.all_active(patron=PATRON)
            for index, row in enumerate(rows):
                age_days = (time.time() - row["written_at"]) / DAY
                print(
                    f"    {index}. [{row['kind']}] {row['text']} "
                    f"(importance {row['importance']:.2f}, {age_days:.0f}d old)"
                )
            print()
            continue

        if user_input == "/compact":
            thread, report = compact(
                thread, budget_tokens=0, keep_recent=KEEP_RECENT, keep_leading=0, client=client
            )
            if report:
                carried += report.anchors
                print(f"    [compacted {report.messages_compacted} messages, "
                      f"{report.tokens_before} -> {report.tokens_after} tokens]")
            else:
                print("    [nothing to compact yet]")
            print()
            continue

        if user_input.startswith("/forget "):
            rows = store.all_active(patron=PATRON)
            try:
                row = rows[int(user_input.split()[1])]
            except (IndexError, ValueError):
                print("    [no memory at that index — try /memories]\n")
                continue
            store.forget(row["memory_id"])
            print(f"    [forgot: {row['text']}]\n")
            continue

        memories = store.recall(user_input, patron=PATRON, k=RECALL_K)
        thread.append({"role": "user", "content": user_input})

        thread, report = compact(
            thread,
            budget_tokens=BUDGET_TOKENS,
            keep_recent=KEEP_RECENT,
            keep_leading=0,
            client=client,
            carried=carried,
        )
        if report:
            carried += report.anchors
            print(f"    [auto-compacted {report.messages_compacted} messages, "
                  f"{report.tokens_before} -> {report.tokens_after} tokens]")

        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": "none"},
            input=build_prompt(thread, memories),
        )
        reply = response.output_text
        thread.append({"role": "assistant", "content": reply})

        print(f"  Agent: {reply}")
        if memories:
            print(f"    [recalled: {memories[0].text} (score {memories[0].score:.2f})]")
        write_turn(user_input, store, patron=PATRON, client=client, verbose=True)
        print()

    print("  Memories at closing time:")
    for row in store.all_active(patron=PATRON):
        print(f"    [{row['kind']}] {row['text']}")
    print()


if __name__ == "__main__":
    demo_memory_agent()
