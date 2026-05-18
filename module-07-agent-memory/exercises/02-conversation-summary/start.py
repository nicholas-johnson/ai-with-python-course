"""
Exercise 02 — Conversation Summary
Extend the memory store with automatic conversation summarisation.
When the session buffer gets too long, older messages are compressed into a summary.

Run:  python start.py
"""
from __future__ import annotations
from dotenv import load_dotenv
from openai import OpenAI

from memory_store import (
    SessionMemory,
    LongTermMemory,
    build_system_prompt,
    chat,
)

load_dotenv()


def summarise_turns(turns: list[dict], client: OpenAI) -> str:
    """Summarise a list of conversation turns into a concise paragraph.

    Args:
        turns: list of {"role": ..., "content": ...} message dicts
        client: OpenAI client instance

    Returns:
        A summary string capturing the key points of the conversation.
    """
    # TODO: implement summarisation
    #   1. Format the turns into a readable transcript string
    #   2. Call client.chat.completions.create with gpt-4o-mini
    #      - system prompt: instruct the model to summarise the conversation
    #        concisely, preserving key facts, decisions, and user preferences
    #      - user message: the formatted transcript
    #   3. Return the summary text from the response
    raise NotImplementedError("TODO")


class SmartSessionMemory(SessionMemory):
    """Session memory that auto-summarises when the buffer gets too long."""

    def __init__(self, max_turns: int = 20, summarise_threshold: int = 10, client: OpenAI | None = None):
        super().__init__(max_turns=max_turns)
        self.summarise_threshold = summarise_threshold
        self.client = client
        self.summary: str = ""

    def add(self, message: dict) -> None:
        # TODO: override add to auto-summarise
        #   1. Call super().add(message) to append normally
        #   2. Check if len(self.messages) > self.summarise_threshold
        #   3. If so, and self.client is set:
        #      a. Take the oldest half of messages
        #      b. Call summarise_turns() on them
        #      c. Prepend the new summary to self.summary
        #      d. Replace the oldest half with a single system message
        #         containing "[Summary of earlier conversation] ..."
        #      e. Keep the recent half intact
        raise NotImplementedError("TODO")

    def get_summary(self) -> str:
        """Return the accumulated conversation summary."""
        return self.summary


def main():
    client = OpenAI()
    session = SmartSessionMemory(max_turns=30, summarise_threshold=10, client=client)
    long_term = LongTermMemory()

    print("=== Smart Memory Chat ===")
    print("Commands: /summary, /turns, /force-summarise, /memories, quit\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break

        if user_input == "/summary":
            s = session.get_summary()
            if s:
                print(f"[Conversation summary]\n{s}\n")
            else:
                print("[No summary yet -- keep chatting!]\n")
            continue

        if user_input == "/turns":
            msgs = session.get_messages()
            print(
                f"[Session buffer: {len(msgs)} messages "
                f"(threshold: {session.summarise_threshold})]\n"
            )
            continue

        if user_input == "/force-summarise":
            if len(session.messages) < 2:
                print("[Not enough messages to summarise]\n")
                continue
            half = len(session.messages) // 2
            old_turns = session.messages[:half]
            summary_text = summarise_turns(old_turns, client)
            session.summary = (
                session.summary + "\n" + summary_text
                if session.summary
                else summary_text
            )
            session.messages = [
                {"role": "system", "content": f"[Summary of earlier conversation] {summary_text}"}
            ] + session.messages[half:]
            print(f"[Summarised {len(old_turns)} messages]\n")
            continue

        if user_input == "/memories":
            entries = long_term.recall()
            if not entries:
                print("[No long-term memories stored]\n")
            else:
                for key, entry in entries:
                    print(
                        f"  {key}: {entry.value} "
                        f"(importance: {entry.importance:.2f})"
                    )
                print()
            continue

        response = chat(user_input, session, long_term, client)
        print(f"Agent: {response}\n")


if __name__ == "__main__":
    main()
