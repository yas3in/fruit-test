"""Automation package for FruitCraft Bot."""

from fruitcraft_bot.automation.battle_worker import AccountState, BattleWorker
from fruitcraft_bot.automation.mine_worker import MineWorker
from fruitcraft_bot.automation.quest_worker import QuestWorker
from fruitcraft_bot.automation.scheduler import AccountContainer, Scheduler

__all__ = [
    "AccountState",
    "BattleWorker",
    "QuestWorker",
    "MineWorker",
    "AccountContainer",
    "Scheduler",
]
