"""
Exercise 07 — Text-to-SQL

Convert natural language questions to SQL queries,
execute them safely, and return results.
"""

import sqlite3
from openai import OpenAI


FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]


def get_schema(db_path: str) -> str:
    """
    Extract the schema from a SQLite database.

    Returns all CREATE TABLE statements as a single string.

    TODO:
    - Connect to the SQLite database
    - Query sqlite_master for type='table'
    - Collect all CREATE TABLE SQL statements
    - Return them joined by newlines
    """
    # TODO: implement schema extraction
    pass


def text_to_sql(client: OpenAI, question: str, schema: str) -> str:
    """
    Generate a SQL SELECT query from a natural language question.

    Args:
        client: OpenAI client.
        question: The user's natural language question.
        schema: The database schema (CREATE TABLE statements).

    Returns:
        A SQL SELECT query string.

    TODO:
    - Prompt gpt-4o-mini with the schema and question
    - Ask it to generate a SQLite SELECT query only
    - Strip any markdown code fences from the response
    - Return the clean SQL string
    """
    # TODO: implement text-to-SQL generation
    pass


def safe_execute(db_path: str, sql: str) -> list[dict]:
    """
    Validate and execute a SQL query safely.

    Args:
        db_path: Path to the SQLite database.
        sql: The SQL query to execute.

    Returns:
        List of result dicts (column names as keys).

    Raises:
        ValueError: If the SQL contains forbidden keywords.

    TODO:
    - Check that none of FORBIDDEN_KEYWORDS appear in the SQL (case-insensitive)
    - Raise ValueError if any are found
    - Execute the query with sqlite3
    - Return results as a list of dicts
    """
    # TODO: implement safe SQL execution
    pass


def ask_database(client: OpenAI, db_path: str, question: str) -> dict:
    """
    Full text-to-SQL pipeline: schema → generate SQL → execute → return.

    Returns:
        Dict with "sql" (the generated query) and "results" (the query results).

    TODO:
    - Get the database schema
    - Generate SQL from the question
    - Execute the SQL safely
    - Return both the SQL and results
    """
    # TODO: implement full pipeline
    pass
