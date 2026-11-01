"""Part 2: Long-term memory with importance decay. No model call.
Run alone:  python module-07-agent-memory/demo/02_long_term_memory.py
"""

import time
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    value: str
    importance: float = 1.0
    timestamp: float = field(default_factory=time.time)
    forgotten: bool = False


class LongTermMemory:
    """Key-value store with importance decay and explicit forget."""

    def __init__(self):
        self._store: dict[str, MemoryEntry] = {}

    def remember(self, key: str, value: str, importance: float = 1.0) -> None:
        self._store[key] = MemoryEntry(value=value, importance=importance)

    def recall(self, prefix: str = "") -> list[tuple[str, MemoryEntry]]:
        results = [
            (k, v) for k, v in self._store.items()
            if not v.forgotten and (not prefix or k.startswith(prefix))
        ]
        return sorted(results, key=lambda item: item[1].importance, reverse=True)

    def forget(self, key: str) -> bool:
        if key in self._store:
            self._store[key].forgotten = True
            return True
        return False

    def tick_decay(self, factor: float = 0.9) -> int:
        removed = 0
        to_delete = []
        for key, entry in self._store.items():
            if not entry.forgotten:
                entry.importance *= factor
                if entry.importance < 0.1:
                    to_delete.append(key)
        for key in to_delete:
            del self._store[key]
            removed += 1
        return removed


def demo_long_term_memory(client=None):
    print("=" * 60)
    print("PART 2: LONG-TERM MEMORY")
    print("=" * 60)
    print()

    memory = LongTermMemory()
    memory.remember("user_name", "Commander Voss", importance=1.0)
    memory.remember("briefing_style", "Prefers concise bullet points", importance=0.8)
    memory.remember("reactor_history", "Ion storm caused 15% drop last month", importance=0.6)

    print("  Stored 3 memories:")
    for key, entry in memory.recall():
        print(f"    {key}: {entry.value} (importance: {entry.importance:.2f})")

    print("\n  Applying decay (factor=0.7) three times...")
    for i in range(3):
        removed = memory.tick_decay(factor=0.7)
        remaining = memory.recall()
        print(f"    Round {i + 1}: {removed} removed, {len(remaining)} remaining")
        for key, entry in remaining:
            print(f"      {key}: importance={entry.importance:.3f}")

    print("\n  Forgetting 'user_name'...")
    memory.forget("user_name")
    print(f"  Recall 'user_name': {[key for key, _ in memory.recall('user_name')]}")
    print()


if __name__ == "__main__":
    demo_long_term_memory()
