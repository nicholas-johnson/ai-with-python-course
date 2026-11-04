"""Build SQLite database from movies.json."""

import json
import sqlite3
import os
from .config import DATA_DIR, DB_PATH


def build_database():
    movies_path = os.path.join(DATA_DIR, "movies.json")
    with open(movies_path) as f:
        movies = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS cast_members;
        DROP TABLE IF EXISTS genres;
        DROP TABLE IF EXISTS movies;

        CREATE TABLE movies (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            year INTEGER,
            director TEXT,
            rating REAL,
            runtime_minutes INTEGER,
            plot TEXT
        );

        CREATE TABLE genres (
            movie_id INTEGER REFERENCES movies(id),
            genre TEXT NOT NULL
        );

        CREATE TABLE cast_members (
            movie_id INTEGER REFERENCES movies(id),
            actor_name TEXT NOT NULL
        );
    """)

    for m in movies:
        cur.execute(
            "INSERT INTO movies VALUES (?, ?, ?, ?, ?, ?, ?)",
            (m["id"], m["title"], m["year"], m["director"],
             m["rating"], m["runtime_minutes"], m["plot"]),
        )
        for g in m.get("genres", []):
            cur.execute("INSERT INTO genres VALUES (?, ?)", (m["id"], g))
        for a in m.get("cast", []):
            cur.execute("INSERT INTO cast_members VALUES (?, ?)", (m["id"], a))

    conn.commit()
    conn.close()
    print(f"Built {DB_PATH} with {len(movies)} movies")


if __name__ == "__main__":
    build_database()
