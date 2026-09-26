"""
Unit test for FruitCraft 10-card fallback rotation and weakest card logic.
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from fruitcraft_bot.bot_actions import (
    get_sorted_weakest_cards,
    is_card_ready,
    parse_cards_list
)


class TestWeakestCardRotation(unittest.TestCase):

    def setUp(self):
        # 12 test cards with mixed levels, powers, and cooldown states
        self.raw_cards = [
            {"id": 101, "name": "Apple Lv2", "level": 2, "power": 50, "defense": 30, "in_cooldown": False},
            {"id": 102, "name": "Lemon Lv1 (Weakest)", "level": 1, "power": 10, "defense": 5, "in_cooldown": True},
            {"id": 103, "name": "Cherry Lv1 (2nd Weakest)", "level": 1, "power": 15, "defense": 10, "in_cooldown": False},
            {"id": 104, "name": "Banana Lv1 (3rd Weakest)", "level": 1, "power": 20, "defense": 10, "in_cooldown": False},
            {"id": 105, "name": "Orange Lv1 (4th)", "level": 1, "power": 25, "defense": 15, "in_cooldown": False},
            {"id": 106, "name": "Peach Lv1 (5th)", "level": 1, "power": 30, "defense": 15, "in_cooldown": False},
            {"id": 107, "name": "Plum Lv1 (6th)", "level": 1, "power": 35, "defense": 20, "in_cooldown": False},
            {"id": 108, "name": "Grape Lv1 (7th)", "level": 1, "power": 40, "defense": 20, "in_cooldown": False},
            {"id": 109, "name": "Kiwi Lv1 (8th)", "level": 1, "power": 45, "defense": 25, "in_cooldown": False},
            {"id": 110, "name": "Berry Lv1 (9th)", "level": 1, "power": 50, "defense": 25, "in_cooldown": False},
            {"id": 111, "name": "Mango Lv1 (10th)", "level": 1, "power": 55, "defense": 30, "in_cooldown": False},
            {"id": 112, "name": "Dragonfruit Lv3", "level": 3, "power": 200, "defense": 100, "in_cooldown": False},
        ]

    def test_sorting_and_top_10_limit(self):
        sorted_10 = get_sorted_weakest_cards(self.raw_cards, limit=10)
        self.assertEqual(len(sorted_10), 10)
        # 1st weakest should be Lemon Lv1 (power 10)
        self.assertEqual(sorted_10[0]["id"], 102)
        # 2nd weakest should be Cherry Lv1 (power 15)
        self.assertEqual(sorted_10[1]["id"], 103)
        # 10th should be Mango Lv1 (power 55)
        self.assertEqual(sorted_10[9]["id"], 111)
        # Card 112 (Dragonfruit) should NOT be in the top 10
        ids = [c["id"] for c in sorted_10]
        self.assertNotIn(112, ids)

    def test_fallback_rotation(self):
        """
        Verify that:
        - Weakest card (102) is checked first.
        - Because 102 is in cooldown, it advances to 2nd weakest (103).
        - 103 is available -> picked!
        """
        candidates = get_sorted_weakest_cards(self.raw_cards, limit=10)
        cooldown_cache = {}

        selected = None
        for c in candidates:
            if is_card_ready(c, cooldown_cache):
                selected = c
                break

        self.assertIsNotNone(selected)
        self.assertEqual(selected["id"], 103, "Should pick 2nd weakest because 1st was in cooldown")

    def test_all_10_in_cooldown_reset(self):
        """
        Verify that if all 10 weakest cards are in cooldown:
        None can be picked in that cycle, so the loop can restart from candidate 0.
        """
        all_in_cd = [dict(c, in_cooldown=True) for c in self.raw_cards]
        candidates = get_sorted_weakest_cards(all_in_cd, limit=10)
        cooldown_cache = {}

        selected = None
        for c in candidates:
            if is_card_ready(c, cooldown_cache):
                selected = c
                break

        self.assertIsNone(selected, "None should be picked when all 10 are in cooldown")


if __name__ == "__main__":
    unittest.main()
