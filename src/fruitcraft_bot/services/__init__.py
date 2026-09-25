"""Services package for FruitCraft game operations."""

from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.battle import (
    BattleService,
    ClosestPowerStrategy,
    CustomStrategy,
    HighestRewardStrategy,
    OpponentStrategy,
    StrongestDefenseStrategy,
    WeakestDefenseStrategy,
)
from fruitcraft_bot.services.cards import (
    CardSelectionStrategy,
    CardService,
    CardsSelection,
    CustomSelectionStrategy,
    SpecificCardsStrategy,
    StrongestCardsStrategy,
    WeakestCardsStrategy,
)
from fruitcraft_bot.services.live_battle import LiveBattleService, LiveBattleState
from fruitcraft_bot.services.mine import MineService, MineStatus
from fruitcraft_bot.services.player import PlayerService
from fruitcraft_bot.services.quest import QuestService
from fruitcraft_bot.services.rankings import RankSnapshot, RankingService
from fruitcraft_bot.services.store import StoreService
from fruitcraft_bot.services.tribe import TribeService

__all__ = [
    "AuthService",
    "PlayerService",
    "BattleService",
    "OpponentStrategy",
    "WeakestDefenseStrategy",
    "StrongestDefenseStrategy",
    "ClosestPowerStrategy",
    "HighestRewardStrategy",
    "CustomStrategy",
    "QuestService",
    "CardService",
    "CardSelectionStrategy",
    "StrongestCardsStrategy",
    "WeakestCardsStrategy",
    "SpecificCardsStrategy",
    "CustomSelectionStrategy",
    "CardsSelection",
    "MineService",
    "MineStatus",
    "RankingService",
    "RankSnapshot",
    "TribeService",
    "LiveBattleService",
    "LiveBattleState",
    "StoreService",
]
