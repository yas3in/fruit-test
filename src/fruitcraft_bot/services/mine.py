"""Mine management service and scheduling calculation."""

import logging
import time
from typing import Any, Dict, Optional
from fruitcraft_bot.api.models import BaseModel, Field

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import CollectGoldResult
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.cards import CardService

logger = logging.getLogger("fruitcraft.services.mine")


class MineStatus(BaseModel):
    """Mine state and collection scheduling metrics."""
    allowed: bool = Field(default=False)
    next_allowed_at: Optional[int] = Field(default=None)
    seconds_until_next: float = Field(default=0.0)
    mine_power: int = Field(default=0)
    mine_capacity: int = Field(default=0)


class MineService:
    """Calculates mine gold collection state and handles execution."""

    def __init__(self, api_client: FruitCraftAPIClient, auth_service: AuthService, card_service: Optional[CardService] = None):
        self.client = api_client
        self.auth = auth_service
        self.cards = card_service or CardService(api_client, auth_service)

    def get_status(self, fallback_capacity: int = 10000, fallback_power: int = 100) -> MineStatus:
        """
        Inspect current mine parameters from player state.
        Determines next collection timestamp and delay seconds.
        """
        now = int(time.time())
        info = self.auth.player_info

        if not info:
            return MineStatus(allowed=False, seconds_until_next=60.0)

        allowed = info.gold_collection_allowed
        allowed_at = info.gold_collection_allowed_at

        # Check mine_info subdict if present
        mine_info = info.mine_info or {}
        capacity = int(mine_info.get("capacity", fallback_capacity))
        power = int(mine_info.get("power", fallback_power))

        seconds_remaining = 0.0
        if allowed_at and allowed_at > now:
            seconds_remaining = float(allowed_at - now)
            allowed = False
        elif not allowed and not allowed_at:
            # Fallback default wait time if status unflagged
            seconds_remaining = 300.0

        return MineStatus(
            allowed=allowed,
            next_allowed_at=allowed_at,
            seconds_until_next=max(0.0, seconds_remaining),
            mine_power=power,
            mine_capacity=capacity,
        )

    async def collect(self) -> CollectGoldResult:
        """Call gold collection endpoint."""
        logger.info("Collecting mine gold...")
        res = await self.cards.collect_gold()
        if self.auth.player_info:
            self.auth.player_info.gold_collection_allowed = res.gold_collection_allowed
            self.auth.player_info.gold_collection_allowed_at = res.gold_collection_allowed_at
        return res
