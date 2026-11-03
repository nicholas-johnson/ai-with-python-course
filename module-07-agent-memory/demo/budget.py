"""Token accounting shared by the demos.

Everything in this module is a move against the context budget, so everything
needs to be able to measure it.
"""

import tiktoken

ENCODING = tiktoken.get_encoding("o200k_base")

# Per-message overhead the API adds for role and delimiters. Approximate, but
# consistent, which is what matters when you are comparing components.
MESSAGE_OVERHEAD = 4


def count_text(text: str) -> int:
    """Tokens in a single string."""
    return len(ENCODING.encode(text))


def count_message(message: dict) -> int:
    """Tokens in one message, including role overhead.

    Handles both plain chat messages and Responses API items such as
    function calls, where the payload is in fields other than ``content``.
    """
    parts = [
        str(message.get("content") or ""),
        str(message.get("arguments") or ""),
        str(message.get("output") or ""),
        str(message.get("name") or ""),
    ]
    return count_text(" ".join(p for p in parts if p)) + MESSAGE_OVERHEAD


def count_messages(messages: list[dict]) -> int:
    """Tokens in a message list."""
    return sum(count_message(m) for m in messages)


def bar(tokens: int, total: int, width: int = 30) -> str:
    """A proportional bar, for printing a budget breakdown."""
    if total <= 0:
        return ""
    filled = round(width * tokens / total)
    return "#" * filled + "." * (width - filled)
