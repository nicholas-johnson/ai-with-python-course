"""Text-to-SQL pipeline — convert natural language to SQL queries."""

import sqlite3
from openai import OpenAI
from .config import OPENAI_MODEL
from .guardrails import validate_sql, sanitize_output

client = OpenAI()


def get_schema(db_path: str) -> str:
    """Introspect SQLite database and return schema as a string."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return "\n\n".join(tables)


def text_to_sql(question: str, schema: str) -> str:
    """Use the LLM to convert a natural-language question into a SQL query."""
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content":
             "You are a SQL expert. Given the database schema below, write a single "
             "SQLite SELECT query that answers the user's question. Return ONLY the "
             "SQL query, no explanation, no markdown fences.\n\n"
             f"Schema:\n{schema}"},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    if sql.startswith("```"):
        sql = sql.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return sql


def safe_execute(db_path: str, sql: str) -> list[dict]:
    """Execute SQL after safety validation. Returns list of row dicts."""
    is_safe, reason = validate_sql(sql)
    if not is_safe:
        raise ValueError(f"Blocked: {reason}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    return sanitize_output(rows)


def format_chart_data(rows: list[dict], question: str) -> dict | None:
    """Suggest a chart type and format data for the frontend."""
    if not rows or len(rows) < 2:
        return None

    columns = list(rows[0].keys())

    label_col = None
    value_cols = []
    for col in columns:
        sample = rows[0][col]
        if isinstance(sample, (int, float)):
            value_cols.append(col)
        elif label_col is None:
            label_col = col

    if not label_col or not value_cols:
        return None

    q_lower = question.lower()
    if any(kw in q_lower for kw in ["over time", "by year", "trend", "per year"]):
        chart_type = "line"
    elif any(kw in q_lower for kw in ["compare", "vs", "top", "most", "best", "highest"]):
        chart_type = "bar"
    elif any(kw in q_lower for kw in ["distribution", "breakdown", "proportion", "share"]):
        chart_type = "pie"
    else:
        chart_type = "bar"

    return {
        "chart_type": chart_type,
        "label_column": label_col,
        "value_columns": value_cols,
        "labels": [row[label_col] for row in rows],
        "datasets": [
            {"label": vc, "data": [row[vc] for row in rows]}
            for vc in value_cols
        ],
    }
