# Exercise 07 — Text-to-SQL

## Recap

Much data lives in relational databases. **Text-to-SQL** lets users query structured data with natural language. The LLM receives the database schema and generates a SQL query. Safety is critical — never execute AI-generated SQL with write permissions.

## Your Task

1. Implement `get_schema(db_path)` — extract the schema from a SQLite database.
2. Implement `text_to_sql(client, question, schema)` — generate SQL from a natural language question.
3. Implement `safe_execute(db_path, sql)` — validate and execute SQL safely.
4. Implement `ask_database(client, db_path, question)` — the full pipeline.

## Steps

1. Open `start.py` and review the functions.
2. Implement `get_schema`: query `sqlite_master` to get CREATE TABLE statements.
3. Implement `text_to_sql`: inject the schema into a prompt, ask for SELECT only.
4. Implement `safe_execute`: reject dangerous SQL keywords, execute read-only queries.
5. Wire it together in `ask_database`.

## Running Tests

```bash
pytest module-11-edge-topics/exercises/07-text-to-sql/test_start.py -v
```

## Stretch Goals

- Add a verification step where the LLM checks its own SQL.
- Support multi-table joins.
- Summarise SQL results in natural language.
