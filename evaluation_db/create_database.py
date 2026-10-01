# ===============================================
# Personalized Learning Platform Database
# ===============================================
#
# Objective:
# Create an SQLite database capable of storing:
# - User profiles
# - Uploaded courses
# - AI generations
# - User feedback
#
# The table definitions live in schema.sql (next to
# this file) so they can be read and reviewed on
# their own. This script just executes them.
#
# Run from anywhere:
#     python evaluation_db/create_database.py
#
# ===============================================

import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = DB_DIR / "schema.sql"
DB_PATH = DB_DIR / "learning_platform.db"


def create_database(db_path=DB_PATH):
    """Create (or open) the SQLite database and apply schema.sql."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    create_database()
    print(f"Database successfully created: {DB_PATH}")
