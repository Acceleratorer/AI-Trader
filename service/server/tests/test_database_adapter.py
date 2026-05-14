import os
import sys


SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from database import _adapt_sql_for_postgres


def test_question_mark_placeholder_conversion():
    sql = "SELECT * FROM agents WHERE id = ? AND name = ?"

    assert _adapt_sql_for_postgres(sql) == (
        "SELECT * FROM agents WHERE id = %s AND name = %s"
    )


def test_question_mark_inside_string_is_not_converted():
    sql = "SELECT '?' AS literal WHERE id = ?"

    assert _adapt_sql_for_postgres(sql) == (
        "SELECT '?' AS literal WHERE id = %s"
    )


def test_sqlite_datetime_now_conversion():
    sql = "created_at TEXT DEFAULT (datetime('now'))"
    adapted = _adapt_sql_for_postgres(sql)

    assert "CURRENT_TIMESTAMP" in adapted


def test_autoincrement_conversion():
    sql = "id INTEGER PRIMARY KEY AUTOINCREMENT"

    assert _adapt_sql_for_postgres(sql) == "id SERIAL PRIMARY KEY"


def test_postgres_adapter_escapes_like_percent_literals():
    query = _adapt_sql_for_postgres(
        "SELECT * FROM signals WHERE content LIKE '%@%' AND title LIKE '%source%' AND id = ?"
    )

    assert "content LIKE '%%@%%'" in query
    assert "title LIKE '%%source%%'" in query
    assert query.endswith("id = %s")


def test_postgres_adapter_preserves_existing_escaped_percent_literals():
    query = _adapt_sql_for_postgres("SELECT * FROM signals WHERE content LIKE '%%引用%%'")

    assert "LIKE '%%引用%%'" in query
