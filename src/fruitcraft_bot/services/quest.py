"""Quest service and q-state MD5 hashing."""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import QuestRequest, QuestResult
from fruitcraft_bot.services.auth import AuthService

logger = logging.getLogger("fruitcraft.services.quest")


class QuestService:
    """Manages quest execution and reward collection."""

    def __init__(self, api_client: FruitCraftAPIClient, auth_service: AuthService):
        self.client = api_client
        self.auth = auth_service

    def compute_check_hash(self) -> Optional[str]:
        """Compute check MD5 hash from previous q state."""
        if not self.auth.q:
            return None
        return hashlib.md5(self.auth.q.encode("utf-8")).hexdigest()

    async def do_quest(self, cards: List[int], hash_val: Optional[str] = None) -> QuestResult:
        """Execute quest request using previous q check hash."""
        check_hash = self.compute_check_hash()
        cards_str = ",".join(str(c) for c in cards)
        payload = {
            "cards": cards_str,
        }
        if check_hash:
            payload["check"] = check_hash
        if hash_val:
            payload["hash"] = hash_val

        logger.info("Executing quest with cards [%s], check=%s", cards_str, check_hash)
        resp = await self.client.request("battle/quest", payload)

        data = resp.data if isinstance(resp.data, dict) else {}

        # Update q state
        if "q" in data:
            self.auth.q = str(data["q"])

        # Update player profile state
        if self.auth.player_info:
            if "gold" in data:
                self.auth.player_info.gold += int(data["gold"])
            if "potion" in data:
                self.auth.player_info.potion = int(data["potion"])
            if "nectar" in data:
                self.auth.player_info.nectar = int(data["nectar"])

        result = QuestResult(
            outcome=bool(data.get("status", True)),
            gold=int(data.get("gold", 0)),
            xp=int(data.get("xp", 0)),
            rank=int(data.get("rank", 0)),
            tribe_rank=int(data.get("tribe_rank", 0)),
            total_quests=int(data.get("total_quests", 0)),
            potion=int(data.get("potion", 0)),
            nectar=int(data.get("nectar", 0)),
            q=self.auth.q,
            needs_captcha=resp.needs_captcha,
        )

        logger.info("Quest complete: gold=%d, xp=%d, potion=%d", result.gold, result.xp, result.potion)
        return result

    async def do_quest_with_hash(self, quest_hash: str, cards: List[int]) -> QuestResult:
        """Execute quest with explicit quest hash string."""
        return await self.do_quest(cards=cards, hash_val=quest_hash)

    async def do_quest_from_serialized_options(self, options: Dict[str, Any]) -> QuestResult:
        """Execute quest using raw options payload dict."""
        cards = options.get("cards", [])
        quest_hash = options.get("hash")
        return await self.do_quest(cards=cards, hash_val=quest_hash)
