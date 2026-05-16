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
    # TODO: Strip and check the SQL string
    # 1. Remove trailing semicolons and whitespace
    # 2. Check if BLOCKED_KEYWORDS appear in the query — if so return (False, reason)
    # 3. Check for multiple statements (more than one ';') — if so return (False, reason)
    # 4. Return (True, "ok") if safe
    pass


def sanitize_output(rows: list[dict], max_rows: int = MAX_ROWS) -> list[dict]:
    """Truncate large result sets and oversized cell values."""
    # TODO: Limit results and truncate long strings
    # 1. Slice rows to max_rows
    # 2. For each row, truncate any string value longer than MAX_CELL_LENGTH
    # 3. Return the sanitized list
    pass
