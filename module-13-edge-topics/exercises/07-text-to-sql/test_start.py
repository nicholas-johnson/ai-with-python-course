"""Tests for Exercise 07 — Text-to-SQL."""

import os
import sqlite3
import tempfile
import pytest
from unittest.mock import MagicMock
from start import get_schema, text_to_sql, safe_execute, ask_database


@pytest.fixture
def test_db():
    """Create a temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE crew (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            deck INTEGER
        )
    """)
    conn.execute("INSERT INTO crew VALUES (1, 'Voss', 'Captain', 1)")
    conn.execute("INSERT INTO crew VALUES (2, 'Chen', 'Engineer', 3)")
    conn.execute("INSERT INTO crew VALUES (3, 'Nakamura', 'Scientist', 5)")
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


class TestGetSchema:
    def test_returns_string(self, test_db):
        schema = get_schema(test_db)
        assert isinstance(schema, str)

    def test_contains_create_table(self, test_db):
        schema = get_schema(test_db)
        assert "CREATE TABLE" in schema

    def test_contains_table_name(self, test_db):
        schema = get_schema(test_db)
        assert "crew" in schema

    def test_contains_columns(self, test_db):
        schema = get_schema(test_db)
        assert "name" in schema
        assert "role" in schema


class TestTextToSql:
    def test_returns_string(self):
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "SELECT * FROM crew WHERE role = 'Captain'"
        client.chat.completions.create.return_value = response

        sql = text_to_sql(client, "Who is the captain?", "CREATE TABLE crew (id, name, role)")
        assert isinstance(sql, str)
        assert "SELECT" in sql.upper()

    def test_strips_markdown_fences(self):
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "```sql\nSELECT * FROM crew\n```"
        client.chat.completions.create.return_value = response

        sql = text_to_sql(client, "List all crew", "CREATE TABLE crew (id, name)")
        assert "```" not in sql
        assert "SELECT" in sql.upper()


class TestSafeExecute:
    def test_executes_select(self, test_db):
        results = safe_execute(test_db, "SELECT name FROM crew WHERE role = 'Captain'")
        assert len(results) == 1
        assert results[0]["name"] == "Voss"

    def test_returns_list_of_dicts(self, test_db):
        results = safe_execute(test_db, "SELECT * FROM crew")
        assert isinstance(results, list)
        assert all(isinstance(r, dict) for r in results)
        assert len(results) == 3

    def test_rejects_drop(self, test_db):
        with pytest.raises(ValueError, match="DROP"):
            safe_execute(test_db, "DROP TABLE crew")

    def test_rejects_delete(self, test_db):
        with pytest.raises(ValueError, match="DELETE"):
            safe_execute(test_db, "DELETE FROM crew WHERE id = 1")

    def test_rejects_update(self, test_db):
        with pytest.raises(ValueError, match="UPDATE"):
            safe_execute(test_db, "UPDATE crew SET name = 'Evil' WHERE id = 1")

    def test_rejects_insert(self, test_db):
        with pytest.raises(ValueError, match="INSERT"):
            safe_execute(test_db, "INSERT INTO crew VALUES (4, 'New', 'Spy', 1)")


class TestAskDatabase:
    def test_returns_dict_with_sql_and_results(self, test_db):
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "SELECT name, role FROM crew"
        client.chat.completions.create.return_value = response

        result = ask_database(client, test_db, "List all crew members")
        assert "sql" in result
        assert "results" in result
        assert isinstance(result["results"], list)
        assert len(result["results"]) == 3
