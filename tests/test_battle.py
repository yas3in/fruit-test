"""Unit tests for Battle service, check MD5 hashing, and strategies."""

import hashlib
import unittest
from fruitcraft_bot.api.models import Opponent
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.battle import (
    BattleService,
    ClosestPowerStrategy,
    HighestRewardStrategy,
    StrongestDefenseStrategy,
    WeakestDefenseStrategy,
)


class TestBattle(unittest.TestCase):
    def test_q_check_hash(self):
        auth = AuthService(None)
        auth.q = "previous_q_state_987"
        battle_service = BattleService(None, auth)

        expected_hash = hashlib.md5(b"previous_q_state_987").hexdigest()
        self.assertEqual(battle_service.compute_check_hash(), expected_hash)

    def test_opponent_selection_strategies(self):
        opponents = [
            Opponent(id="1", name="Weak", def_power=1000, gold=500),
            Opponent(id="2", name="Medium", def_power=3000, gold=5000),
            Opponent(id="3", name="Strong", def_power=10000, gold=2000),
        ]

        weakest = WeakestDefenseStrategy().select_opponent(opponents)
        self.assertEqual(weakest.id, "1")

        strongest = StrongestDefenseStrategy().select_opponent(opponents)
        self.assertEqual(strongest.id, "3")

        highest_gold = HighestRewardStrategy().select_opponent(opponents)
        self.assertEqual(highest_gold.id, "2")

        closest = ClosestPowerStrategy(target_power=2800).select_opponent(opponents)
        self.assertEqual(closest.id, "2")

    def test_strongest_cards_strategy_filtering(self):
        from fruitcraft_bot.api.models import CardModel
        from fruitcraft_bot.services.cards import StrongestCardsStrategy
        import time

        now = int(time.time())
        c1 = CardModel(id=1, power=100, in_cooldown=False)
        c2 = CardModel(id=2, power=999, in_cooldown=True)  # Strongest but in cooldown!
        c3 = CardModel(id=3, power=500, in_cooldown=False)

        sel = StrongestCardsStrategy().select([c1, c2, c3], count=2)
        # Should select c3 (power 500) and c1 (power 100), skipping c2 because it's in cooldown
        self.assertEqual(sel.cards, [3, 1])


if __name__ == "__main__":
    unittest.main()
