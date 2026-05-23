from __future__ import annotations

import unittest

from backend.api.mock_service import DEFAULT_STRATEGY_ID, list_rankings


class GeneratedRankingsTest(unittest.TestCase):
    def test_daily_api_rankings_prefer_generated_sample(self) -> None:
        items, total = list_rankings(
            market="cn",
            frequency="daily",
            top_n=20,
            strategy_id=DEFAULT_STRATEGY_ID,
            page=1,
            page_size=20,
        )

        self.assertGreaterEqual(total, 1)
        self.assertEqual(items[0]["symbol"], "000001.SZ")
        self.assertEqual(items[0]["name"], "平安银行")
        self.assertIsInstance(items[0]["positive_factors"][0], str)


if __name__ == "__main__":
    unittest.main()
