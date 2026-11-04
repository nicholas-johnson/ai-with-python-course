"""Text-to-SQL pipeline — convert natural language to SQL queries."""

import sqlite3
from openai import OpenAI
from .config import OPENAI_MODEL
from .guardrails import validate_sql, sanitize_output

client = OpenAI()


def get_schema(db_path: str) -> str:
    """Introspect SQLite database and return schema as a string."""
    # TODO: Read the database schema
    # 1. Connect to the SQLite database
    # 2. Query sqlite_master for CREATE TABLE statements
    # 3. Join them with double newlines and return
    pass


def text_to_sql(question: str, schema: str) -> str:
    """Use the LLM to convert a natural-language question into a SQL query."""
    # TODO: Generate SQL from natural language
    # 1. Call the LLM with a system prompt containing the schema
    # 2. Ask it to return ONLY a SQLite SELECT query, no markdown fences
    # 3. Strip any accidental markdown code fences from the response
    # 4. Return the clean SQL string
    pass


def safe_execute(db_path: str, sql: str) -> list[dict]:
    """Execute SQL after safety validation. Returns list of row dicts."""
    # TODO: Validate and execute the SQL
    # 1. Call validate_sql() — raise ValueError if not safe
    # 2. Connect with sqlite3, set row_factory to sqlite3.Row
    # 3. Execute the query and fetch all rows as dicts
    # 4. Pass through sanitize_output() and return
    pass


def format_chart_data(rows: list[dict], question: str) -> dict | None:
    """Suggest a chart type and format data for the frontend."""
    if not rows or len(rows) < 2:
        return None

    columns = list(rows[0].keys())

    # TODO: Detect chart-worthy data and suggest visualization
    # 1. Identify label_col (first string column) and value_cols (numeric columns)
    # 2. If either is missing, return None
    # 3. Pick chart_type based on keywords in the question:
    #    - "over time", "by year", "trend" → "line"
    #    - "compare", "top", "most", "best" → "bar"
    #    - "distribution", "breakdown", "proportion" → "pie"
    #    - default → "bar"
    # 4. Return {chart_type, label_column, value_columns, labels, datasets}
    pass
