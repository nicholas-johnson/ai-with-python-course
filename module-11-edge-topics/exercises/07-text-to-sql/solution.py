"""
Exercise 07 — Text-to-SQL (Solution)

Convert natural language questions to SQL queries,
execute them safely, and return results.
"""

import sqlite3
from openai import OpenAI


FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]


def get_schema(db_path: str) -> str:
    """
    Extract the schema from a SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    )
    schemas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return "\n\n".join(schemas)


def text_to_sql(client: OpenAI, question: str, schema: str) -> str:
    """
    Generate a SQL SELECT query from a natural language question.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a SQL expert. Given a database schema and a question, "
                    f"generate a SQLite SELECT query that answers the question. "
                    f"Return ONLY the SQL query, no explanation, no markdown.\n\n"
                    f"Schema:\n{schema}"
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.strip("```sql").strip("```").strip()
    return sql


def safe_execute(db_path: str, sql: str) -> list[dict]:
    """
    Validate and execute a SQL query safely.
    """
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            raise ValueError(f"Forbidden SQL keyword detected: {keyword}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def ask_database(client: OpenAI, db_path: str, question: str) -> dict:
    """
    Full text-to-SQL pipeline.
    """
    schema = get_schema(db_path)
    sql = text_to_sql(client, question, schema)
    results = safe_execute(db_path, sql)
    return {"sql": sql, "results": results}
