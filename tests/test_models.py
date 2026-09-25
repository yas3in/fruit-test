"""Unit tests for API models."""

import unittest
from fruitcraft_bot.api.models import (
    APIResponse,
    BattleResult,
    CardModel,
    CollectGoldResult,
    Opponent,
    PlayerInfo,
    PlayerLoadRequest,
    QuestResult,
)


class TestModels(unittest.TestCase):
    def test_player_load_request_defaults(self):
        req = PlayerLoadRequest(restore_key="key_123")
        self.assertEqual(req.game_version, "1.9.10691")
        self.assertEqual(req.os_type, 2)
        self.assertEqual(req.store_type, "myket")
        self.assertEqual(req.restore_key, "key_123")

    def test_api_response_parsing(self):
        resp = APIResponse(status=True, data={"id": "100", "name": "Apple"})
        self.assertTrue(resp.status)
        self.assertEqual(resp.data["id"], "100")

    def test_opponent_model(self):
        opp = Opponent(id="456", name="BananaHero", def_power=5000, gold=12000)
        self.assertEqual(opp.id, "456")
        self.assertEqual(opp.def_power, 5000)
        self.assertEqual(opp.gold, 12000)

    def test_battle_result_model(self):
        res = BattleResult(won=True, gold_earned=500, xp_earned=20, q="new_q_val")
        self.assertTrue(res.won)
        self.assertEqual(res.gold_earned, 500)
        self.assertEqual(res.q, "new_q_val")

    def test_collect_gold_result_model(self):
        res = CollectGoldResult(collected_gold=300, player_gold=5000, gold_collection_allowed=False, gold_collection_allowed_at=1700000000)
        self.assertEqual(res.collected_gold, 300)
        self.assertEqual(res.player_gold, 5000)
        self.assertFalse(res.gold_collection_allowed)
        self.assertEqual(res.gold_collection_allowed_at, 1700000000)

    def test_card_usable_check(self):
        import time
        now = int(time.time())
        card_ready = CardModel(id=101, power=500, in_cooldown=False)
        card_cd = CardModel(id=102, power=800, in_cooldown=True)
        card_future = CardModel(id=103, power=900, in_cooldown=False, cooldown_ends_at=now + 300)

        self.assertTrue(card_ready.is_usable(now))
        self.assertFalse(card_cd.is_usable(now))
        self.assertFalse(card_future.is_usable(now))


if __name__ == "__main__":
    unittest.main()
