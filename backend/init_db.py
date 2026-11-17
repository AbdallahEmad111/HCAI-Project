import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CORPUS_PATH = DATA_DIR / "corpus.json"
DB_PATH = DATA_DIR / "research.db"


def init_database():
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS papers")
    cur.execute("DROP TABLE IF EXISTS papers_fts")
    cur.execute("DROP TABLE IF EXISTS venues")

    cur.execute("""
        CREATE TABLE papers (
            paper_id TEXT PRIMARY KEY,
            department TEXT NOT NULL,
            subfield TEXT NOT NULL,
            title TEXT NOT NULL,
            authors TEXT NOT NULL,
            year INTEGER NOT NULL,
            venue TEXT NOT NULL,
            doi TEXT NOT NULL,
            url TEXT NOT NULL,
            license TEXT NOT NULL,
            required_skills TEXT NOT NULL,
            compute_level TEXT NOT NULL,
            methods TEXT NOT NULL,
            findings TEXT NOT NULL,
            documented_limitations TEXT NOT NULL,
            suggested_direction TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE VIRTUAL TABLE papers_fts USING fts5(
            paper_id UNINDEXED,
            department,
            subfield,
            title,
            required_skills,
            methods,
            documented_limitations,
            suggested_direction
        )
    """)

    cur.execute("""
        CREATE TABLE venues (
            venue_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            departments TEXT NOT NULL,
            focus TEXT NOT NULL,
            official_url TEXT NOT NULL,
            last_verified TEXT NOT NULL,
            note TEXT NOT NULL
        )
    """)

    for p in corpus["papers"]:
        skills_str = ", ".join(p["required_skills"])
        cur.execute("""
            INSERT INTO papers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["paper_id"], p["department"], p["subfield"], p["title"],
            p["authors"], p["year"], p["venue"], p["doi"], p["url"],
            p["license"], skills_str, p["compute_level"], p["methods"],
            p["findings"], p["documented_limitations"], p["suggested_direction"]
        ))

        cur.execute("""
            INSERT INTO papers_fts VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["paper_id"], p["department"], p["subfield"], p["title"],
            skills_str, p["methods"], p["documented_limitations"],
            p["suggested_direction"]
        ))

    for v in corpus["venues"]:
        depts_str = ", ".join(v["departments"])
        cur.execute("""
            INSERT INTO venues VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            v["venue_id"], v["name"], depts_str, v["focus"],
            v["official_url"], v["last_verified"], v["note"]
        ))

    conn.commit()
    conn.close()
    print(f"Database created at: {DB_PATH}")
    print(f"Inserted {len(corpus['papers'])} papers and {len(corpus['venues'])} venues.")


if __name__ == "__main__":
    init_database()