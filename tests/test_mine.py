"""Unit tests for Mine service and timing calculations."""

import time
import unittest
from fruitcraft_bot.api.models import PlayerInfo
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.mine import MineService


class TestMine(unittest.TestCase):
    def test_mine_status_calculation(self):
        auth = AuthService(None)
        now = int(time.time())

        # Case 1: Collection allowed
        auth.player_info = PlayerInfo(
            gold_collection_allowed=True,
            gold_collection_allowed_at=None,
        )
        mine_service = MineService(None, auth)
        status = mine_service.get_status()
        self.assertTrue(status.allowed)
        self.assertEqual(status.seconds_until_next, 0.0)

        # Case 2: Collection locked until future timestamp
        future = now + 120
        auth.player_info = PlayerInfo(
            gold_collection_allowed=False,
            gold_collection_allowed_at=future,
        )
        status2 = mine_service.get_status()
        self.assertFalse(status2.allowed)
        self.assertGreater(status2.seconds_until_next, 100.0)


if __name__ == "__main__":
    unittest.main()
