# Exercise 07 — Text-to-SQL

## Recap

### The problem: data locked in databases

Much of the world's useful data lives in relational databases (SQL). Non-technical users can't query it, and even developers find it tedious to write complex SQL. **Text-to-SQL** lets users ask questions in plain English and get answers from the database.

### How it works

The pipeline has four steps:

1. **Get the schema** — read the database structure (table names, column names, types) so the LLM knows what's available.
2. **Generate SQL** — send the question + schema to the LLM, which writes a SELECT query.
3. **Validate** — check the generated SQL for dangerous keywords (DROP, DELETE, etc.) before running it.
4. **Execute** — run the safe query and return the results.

### Schema injection

The LLM can't see your database — you have to tell it what tables and columns exist. You do this by extracting the `CREATE TABLE` statements and putting them in the system prompt:

```python
schema = """
CREATE TABLE crew (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    rank TEXT
);

CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY,
    sensor_name TEXT,
    value REAL,
    timestamp TEXT
);
"""
```

The LLM reads this and knows it can write queries like `SELECT name FROM crew WHERE department = 'engineering'`.

### Why safety matters

The LLM generates arbitrary SQL. If you run it without checking, a hallucinated `DROP TABLE crew` would delete your data. **Never execute AI-generated SQL with write permissions.** Always:

- Check for forbidden keywords (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE).
- Use a read-only database connection if possible.
- Wrap execution in a try/except.

## What you build

Four functions in **`start.py`**:

| Function | What it does |
|---|---|
| `get_schema(db_path)` | Read CREATE TABLE statements from a SQLite database |
| `text_to_sql(client, question, schema)` | Give the LLM the schema + question, get back a SQL query |
| `safe_execute(db_path, sql)` | Validate the SQL is safe, then run it |
| `ask_database(client, db_path, question)` | Full pipeline: schema → generate → validate → execute |

## Data format

The SQLite database is just a file on disk. You access it with Python's built-in `sqlite3` module:

```python
import sqlite3
conn = sqlite3.connect("data/ship.db")
```

`get_schema` returns a string of CREATE TABLE statements. `text_to_sql` returns a SQL string like:

```sql
SELECT name, department FROM crew WHERE rank = 'Lieutenant'
```

`safe_execute` returns the results as a list of dicts:

```python
[
    {"name": "Torres", "department": "engineering"},
    {"name": "Kim", "department": "operations"},
]
```

The final `ask_database` returns both the SQL and results:

```python
{"sql": "SELECT name, department FROM crew WHERE rank = 'Lieutenant'", "results": [...]}
```

## Step-by-step

### 1. Implement `get_schema`

Query the SQLite internal table `sqlite_master` to get all CREATE TABLE statements:

```python
def get_schema(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
    )
    schemas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return "\n\n".join(schemas)
```

### 2. Implement `text_to_sql`

Put the schema in the system message and the question in the user message. Tell the model to return ONLY the SQL, no explanation:

```python
messages = [
    {
        "role": "system",
        "content": (
            "You are a SQL expert. Given a database schema and a question, "
            "generate a SQLite SELECT query that answers the question. "
            "Return ONLY the SQL query, no explanation, no markdown.\n\n"
            f"Schema:\n{schema}"
        ),
    },
    {"role": "user", "content": question},
]
```

> **Important:** The model sometimes wraps SQL in markdown code fences (` ```sql ... ``` `). Strip those if present.

### 3. Implement `safe_execute`

Check for dangerous keywords, then execute:

```python
FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]

def safe_execute(db_path: str, sql: str) -> list[dict]:
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            raise ValueError(f"Forbidden SQL keyword detected: {keyword}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    cursor = conn.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
```

### 4. Implement `ask_database`

Wire it all together:

```python
def ask_database(client, db_path, question):
    schema = get_schema(db_path)
    sql = text_to_sql(client, question, schema)
    results = safe_execute(db_path, sql)
    return {"sql": sql, "results": results}
```

## Try it

```bash
cd module-11-edge-topics/exercises/07-text-to-sql
python start.py
```

Try: "How many crew members are in engineering?", "What's the highest sensor reading?", "List all crew sorted by rank."

## Running Tests

```bash
pytest module-11-edge-topics/exercises/07-text-to-sql/test_start.py -v
```

## Stretch Goals

- Add a verification step where the LLM checks its own SQL before execution.
- Support multi-table joins.
- Summarise SQL results in natural language ("There are 12 crew members in engineering").
