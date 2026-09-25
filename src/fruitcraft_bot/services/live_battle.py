"""Live battle service and help/card assignment routines."""

import logging
import time
from typing import Any, Dict, Optional
from fruitcraft_bot.api.models import BaseModel, Field

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import LiveBattleHelpRequest, LiveBattleRequest, SetCardForLiveBattleRequest

logger = logging.getLogger("fruitcraft.services.live_battle")


class LiveBattleState(BaseModel):
    """Tracks current live battle round state."""
    battle_id: Optional[str] = Field(default=None)
    help_cost: int = Field(default=0)
    round: int = Field(default=1)
    card: Optional[int] = Field(default=None)
    last_used_at: int = Field(default_factory=lambda: int(time.time()))


class LiveBattleService:
    """Independent live battle service."""

    def __init__(self, api_client: FruitCraftAPIClient):
        self.client = api_client
        self.state = LiveBattleState()

    async def help(self, battle_id: str) -> Dict[str, Any]:
        """Request live battle help (POST live-battle/help)."""
        req = LiveBattleHelpRequest(battle_id=battle_id)
        logger.info("Requesting live battle help for battle_id: %s", battle_id)
        resp = await self.client.request("live-battle/help", req)
        data = resp.data if isinstance(resp.data, dict) else {}
        self.state.battle_id = battle_id
        if "help_cost" in data:
            self.state.help_cost = int(data["help_cost"])
        return data

    async def set_card_for_live_battle(self, round_num: int, card_id: int, battle_id: str) -> Dict[str, Any]:
        """Set card for live battle round (POST live-battle/setcardforlivebattle)."""
        req = SetCardForLiveBattleRequest(round=round_num, card=card_id, battle_id=battle_id)
        logger.info("Setting card %d for live battle %s (Round %d)...", card_id, battle_id, round_num)
        resp = await self.client.request("live-battle/setcardforlivebattle", req)
        data = resp.data if isinstance(resp.data, dict) else {}
        self.state.round = round_num
        self.state.card = card_id
        self.state.last_used_at = int(time.time())
        return data

    async def live_battle(self, opponent_id: str) -> Dict[str, Any]:
        """Initiate live battle against opponent (POST live-battle/livebattle)."""
        req = LiveBattleRequest(opponent_id=opponent_id)
        logger.info("Initiating live battle against opponent_id: %s", opponent_id)
        resp = await self.client.request("live-battle/livebattle", req)
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}
