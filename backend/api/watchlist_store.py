from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_WATCHLIST = {
    "viewer": [
        {
            "symbol": "600519.SH",
            "note": "长期观察行业龙头",
            "created_at": "2026-05-22T20:00:00+08:00",
        }
    ],
    "researcher": [
        {
            "symbol": "00700.HK",
            "note": "观察港股互联网权重股",
            "created_at": "2026-05-22T20:05:00+08:00",
        }
    ],
    "admin": [],
}


class WatchlistStore:
    def __init__(self, db_path: str | Path = "data/local/mm2.sqlite3") -> None:
        self.db_path = Path(db_path)
        self._initialized = False

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        if self._initialized:
            return
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS watchlist_items (
                    username TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (username, symbol)
                )
                """
            )
            count = connection.execute("SELECT COUNT(*) FROM watchlist_items").fetchone()[0]
            if count == 0:
                self._seed_defaults(connection)
        self._initialized = True

    def _seed_defaults(self, connection: sqlite3.Connection) -> None:
        rows = []
        for username, entries in DEFAULT_WATCHLIST.items():
            for entry in entries:
                rows.append(
                    (
                        username,
                        entry["symbol"].upper(),
                        entry.get("note"),
                        entry["created_at"],
                    )
                )
        if rows:
            connection.executemany(
                """
                INSERT OR IGNORE INTO watchlist_items (username, symbol, note, created_at)
                VALUES (?, ?, ?, ?)
                """,
                rows,
            )

    def list_entries(self, username: str) -> list[dict]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT symbol, note, created_at
                FROM watchlist_items
                WHERE username = ?
                ORDER BY created_at ASC, symbol ASC
                """,
                (username,),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_entry(self, username: str, symbol: str, note: Optional[str]) -> Optional[str]:
        self.initialize()
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO watchlist_items (username, symbol, note, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, symbol.upper(), note, created_at),
            )
        if cursor.rowcount != 1:
            return None
        return created_at

    def remove_entry(self, username: str, symbol: str) -> bool:
        self.initialize()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM watchlist_items
                WHERE username = ? AND symbol = ?
                """,
                (username, symbol.upper()),
            )
        return cursor.rowcount == 1

    def replace_entries(self, username: str, entries: Iterable[dict]) -> None:
        self.initialize()
        with self._connect() as connection:
            connection.execute("DELETE FROM watchlist_items WHERE username = ?", (username,))
            connection.executemany(
                """
                INSERT OR IGNORE INTO watchlist_items (username, symbol, note, created_at)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        username,
                        entry["symbol"].upper(),
                        entry.get("note"),
                        entry.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    )
                    for entry in entries
                ],
            )


watchlist_store = WatchlistStore()
