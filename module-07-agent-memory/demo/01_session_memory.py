"""Part 1: A capped message list. No model call.
Run alone:  python module-07-agent-memory/demo/01_session_memory.py
"""


class SessionMemory:
    """Capped message buffer — oldest messages are evicted first."""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: list[dict] = []

    def add(self, message: dict) -> None:
        self.messages.append(message)
        while len(self.messages) > self.max_turns:
            self.messages.pop(0)

    def get_messages(self) -> list[dict]:
        return list(self.messages)


def demo_session_memory(client=None):
    print("=" * 60)
    print("PART 1: SESSION MEMORY")
    print("=" * 60)
    print()

    session = SessionMemory(max_turns=4)
    messages = [
        {"role": "user", "content": "What's the reactor status?"},
        {"role": "assistant", "content": "Reactor is at 98% efficiency."},
        {"role": "user", "content": "Any anomalies?"},
        {"role": "assistant", "content": "No anomalies detected."},
        {"role": "user", "content": "Check the navigation array."},
    ]

    for msg in messages:
        session.add(msg)
        print(f"  Added: {msg['role']}: {msg['content'][:60]}")
        print(f"  Buffer size: {len(session.get_messages())} / {session.max_turns}")

    print(f"\n  Final buffer ({len(session.get_messages())} messages):")
    for message in session.get_messages():
        print(f"    {message['role']}: {message['content']}")
    print()


if __name__ == "__main__":
    demo_session_memory()
