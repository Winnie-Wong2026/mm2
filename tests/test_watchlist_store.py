from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.api.watchlist_store import WatchlistStore


class WatchlistStoreTest(unittest.TestCase):
    def test_add_remove_and_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "watchlist.sqlite3"
            store = WatchlistStore(db_path)

            created_at = store.add_entry("alice", "00700.hk", "observe Tencent")

            self.assertIsNotNone(created_at)
            self.assertEqual(
                store.list_entries("alice"),
                [{"symbol": "00700.HK", "note": "observe Tencent", "created_at": created_at}],
            )

            reopened = WatchlistStore(db_path)
            self.assertEqual(reopened.list_entries("alice")[0]["symbol"], "00700.HK")
            self.assertIsNone(reopened.add_entry("alice", "00700.HK", "duplicate"))
            self.assertTrue(reopened.remove_entry("alice", "00700.HK"))
            self.assertFalse(reopened.remove_entry("alice", "00700.HK"))


if __name__ == "__main__":
    unittest.main()
