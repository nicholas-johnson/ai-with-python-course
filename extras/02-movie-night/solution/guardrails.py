"""SQL safety guardrails — validates queries and limits output size."""

import re

BLOCKED_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|DETACH)\b",
    re.IGNORECASE,
)

MAX_ROWS = 200
MAX_CELL_LENGTH = 500


def validate_sql(sql: str) -> tuple[bool, str]:
    """Return (is_safe, reason). Blocks any mutation statements."""
    stripped = sql.strip().rstrip(";")
    if BLOCKED_KEYWORDS.search(stripped):
        return False, "Query contains a blocked keyword (mutation not allowed)"
    if stripped.count(";") > 0:
        return False, "Multiple statements are not allowed"
    return True, "ok"


def sanitize_output(rows: list[dict], max_rows: int = MAX_ROWS) -> list[dict]:
    """Truncate large result sets and oversized cell values."""
    truncated = rows[:max_rows]
    sanitized = []
    for row in truncated:
        sanitized.append({
            k: (str(v)[:MAX_CELL_LENGTH] + "..." if isinstance(v, str) and len(v) > MAX_CELL_LENGTH else v)
            for k, v in row.items()
        })
    return sanitized
