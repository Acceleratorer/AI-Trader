import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

import database
from routes import create_app


class SignalFeedFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        database.DATABASE_URL = ""
        database._SQLITE_DB_PATH = os.path.join(self.tmp.name, "test.db")
        database.init_database()
        self.client = TestClient(create_app())
        self.agent_id = self._create_agent()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _create_agent(self) -> int:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO agents (name, token, cash, created_at, updated_at)
            VALUES (?, ?, 100000.0, ?, ?)
            """,
            ("feed-agent", "feed-token", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        agent_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return agent_id

    def _insert_signal(self, signal_id: int, message_type: str, symbol: str = None, symbols: str = None) -> None:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO signals (
                signal_id, agent_id, message_type, market, signal_type, symbol,
                symbols, title, content, timestamp, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                self.agent_id,
                message_type,
                "crypto",
                "realtime" if message_type == "operation" else message_type,
                symbol,
                symbols,
                f"{symbol or symbols} setup",
                "filter fixture",
                signal_id,
                f"2026-01-01T00:0{signal_id}:00Z",
            ),
        )
        conn.commit()
        conn.close()

    def test_signal_feed_filters_by_symbol_and_strategy_symbols(self) -> None:
        self._insert_signal(1, "operation", symbol="BTC")
        self._insert_signal(2, "operation", symbol="ETH")
        self._insert_signal(3, "strategy", symbols="BTC,SOL")

        response = self.client.get("/api/signals/feed?symbol=BTC")

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual({item["signal_id"] for item in data["signals"]}, {1, 3})


if __name__ == "__main__":
    unittest.main()
