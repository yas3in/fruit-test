"""Automation package for FruitCraft Bot."""

from src.fruitcraft_bot.automation.base_worker import BaseWorker
from src.fruitcraft_bot.automation.battle_worker import BattleWorker
from src.fruitcraft_bot.automation.mine_worker import MineWorker
from src.fruitcraft_bot.automation.quest_worker import QuestWorker
from src.fruitcraft_bot.automation.worker_manager import worker_manager, WorkerManager

__all__ = [
    "BaseWorker",
    "BattleWorker",
    "MineWorker",
    "QuestWorker",
    "worker_manager",
    "WorkerManager"
]
