"""Battle service, state management, and opponent selection strategies."""

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from fruitcraft_bot.api.models import BaseModel

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import BattleRequest, BattleResult, Opponent
from fruitcraft_bot.config import BattleConfig
from fruitcraft_bot.services.auth import AuthService

logger = logging.getLogger("fruitcraft.services.battle")


# ============================================================================
# Opponent Selection Strategies
# ============================================================================

class OpponentStrategy(ABC):
    """Abstract base class for opponent selection strategies."""

    @abstractmethod
    def select_opponent(self, opponents: List[Opponent], config: Optional[BattleConfig] = None) -> Optional[Opponent]:
        pass


class WeakestDefenseStrategy(OpponentStrategy):
    """Select opponent with lowest defense power."""

    def select_opponent(self, opponents: List[Opponent], config: Optional[BattleConfig] = None) -> Optional[Opponent]:
        if not opponents:
            return None
        return min(opponents, key=lambda o: o.def_power)


class StrongestDefenseStrategy(OpponentStrategy):
    """Select opponent with highest defense power."""

    def select_opponent(self, opponents: List[Opponent], config: Optional[BattleConfig] = None) -> Optional[Opponent]:
        if not opponents:
            return None
        return max(opponents, key=lambda o: o.def_power)


class ClosestPowerStrategy(OpponentStrategy):
    """Select opponent with defense power closest to player's power ratio."""

    def __init__(self, target_power: int = 1000):
        self.target_power = target_power

    def select_opponent(self, opponents: List[Opponent], config: Optional[BattleConfig] = None) -> Optional[Opponent]:
        if not opponents:
            return None
        return min(opponents, key=lambda o: abs(o.def_power - self.target_power))


class HighestRewardStrategy(OpponentStrategy):
    """Select opponent offering maximum gold reward."""

    def select_opponent(self, opponents: List[Opponent], config: Optional[BattleConfig] = None) -> Optional[Opponent]:
        if not opponents:
            return None
        return max(opponents, key=lambda o: o.gold)


class CustomStrategy(OpponentStrategy):
    """Select opponent matching custom BattleConfig bounds."""

    def select_opponent(self, opponents: List[Opponent], config: Optional[BattleConfig] = None) -> Optional[Opponent]:
        if not opponents:
            return None
        cfg = config or BattleConfig()

        candidates = [o for o in opponents if o.gold >= cfg.minimum_gold]
        if not candidates:
            candidates = opponents

        if cfg.prefer_low_defense:
            return min(candidates, key=lambda o: o.def_power)
        elif cfg.prefer_gold:
            return max(candidates, key=lambda o: o.gold)

        return candidates[0]


STRATEGY_MAP = {
    "weakest": WeakestDefenseStrategy(),
    "strongest": StrongestDefenseStrategy(),
    "closest": ClosestPowerStrategy(),
    "highest_reward": HighestRewardStrategy(),
    "custom": CustomStrategy(),
}


# ============================================================================
# Battle Service
# ============================================================================

class BattleService:
    """Handles battle operations with q-state MD5 hashing and per-account locking."""

    def __init__(self, api_client: FruitCraftAPIClient, auth_service: AuthService):
        self.client = api_client
        self.auth = auth_service
        self._lock = asyncio.Lock()

    async def get_opponents(self) -> List[Opponent]:
        """Fetch list of potential battle opponents."""
        logger.info("Fetching opponents...")
        resp = await self.client.request("battle/getopponents", {})
        opponents = []

        data = resp.data
        raw_list = []
        if isinstance(data, list):
            raw_list = data
        elif isinstance(data, dict):
            raw_list = data.get("opponents", data.get("players", []))

        for item in raw_list:
            if isinstance(item, dict):
                opponents.append(
                    Opponent(
                        id=str(item.get("id", "")),
                        name=str(item.get("name", "Unknown")),
                        rank=int(item.get("rank", 0)),
                        xp=int(item.get("xp", 0)),
                        gold=int(item.get("gold", 0)),
                        level=int(item.get("level", 1)),
                        def_power=int(item.get("def_power", item.get("power", 0))),
                        league_id=int(item.get("league_id", 0)),
                        league_rank=int(item.get("league_rank", 0)),
                        avatar_id=int(item.get("avatar_id", 0)),
                        power_ratio=float(item.get("power_ratio", 1.0)),
                        tribe_name=item.get("tribe_name"),
                    )
                )

        logger.info("Found %d opponents.", len(opponents))
        return opponents

    async def get_opponents_from_other_passport(self, passport: str) -> List[Opponent]:
        """Fetch opponents using alternative passport cookie."""
        logger.info("Fetching opponents using alternate passport...")
        resp = await self.client.request("battle/getopponents", {}, passport=passport)
        # Parse same response structure
        opponents = []
        data = resp.data
        raw_list = data if isinstance(data, list) else (data.get("opponents", []) if isinstance(data, dict) else [])
        for item in raw_list:
            if isinstance(item, dict):
                opponents.append(Opponent(id=str(item.get("id", "")), name=str(item.get("name", "")), def_power=int(item.get("def_power", 0))))
        return opponents

    def compute_check_hash(self) -> Optional[str]:
        """Compute check MD5 hash from previous q state."""
        if not self.auth.q:
            return None
        return hashlib.md5(self.auth.q.encode("utf-8")).hexdigest()

    async def battle(
        self,
        opponent_id: str,
        cards: List[int],
        hero_id: Optional[int] = None,
    ) -> BattleResult:
        """
        Execute battle sequentially under lock.
        Calculates check = MD5(previous_q) and updates q upon completion.
        """
        async with self._lock:
            check_hash = self.compute_check_hash()
            cards_str = ",".join(str(c) for c in cards)
            payload = {
                "opponent_id": str(opponent_id),
                "cards": cards_str,
            }
            if check_hash:
                payload["check"] = check_hash
            if hero_id is not None:
                payload["hero_id"] = hero_id

            logger.info("Executing battle against opponent %s with cards [%s], check=%s", opponent_id, cards_str, check_hash)
            resp = await self.client.request("battle/battle", payload)

            data = resp.data if isinstance(resp.data, dict) else {}

            # Update q state
            new_q = data.get("q")
            if new_q:
                self.auth.q = str(new_q)

            # Update gold/xp in player info
            if self.auth.player_info:
                if "player_gold" in data:
                    self.auth.player_info.gold = int(data["player_gold"])
                elif "gold" in data:
                    self.auth.player_info.gold += int(data["gold"])

            result = BattleResult(
                won=bool(data.get("won", data.get("result", False))),
                gold_earned=int(data.get("gold", 0)),
                xp_earned=int(data.get("xp", 0)),
                opp_name=str(data.get("opp_name", "")),
                q=self.auth.q,
                cards_damaged=data.get("cards_damaged", []),
                needs_captcha=resp.needs_captcha,
            )

            logger.info("Battle result: won=%s, gold_earned=%d, xp_earned=%d", result.won, result.gold_earned, result.xp_earned)
            return result
