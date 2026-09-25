"""Player information and management service."""

import logging
from typing import Any, Dict, Optional, Union
from fruitcraft_bot.config import SecretStr

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import FillPotionRequest, PlayerInfo, PlayerLoadRequest
from fruitcraft_bot.config import DeviceConfig
from fruitcraft_bot.services.auth import AuthService

logger = logging.getLogger("fruitcraft.services.player")


class PlayerService:
    """Manages player profile state and related endpoints."""

    def __init__(self, api_client: FruitCraftAPIClient, auth_service: Optional[AuthService] = None):
        self.client = api_client
        self.auth = auth_service or AuthService(api_client)

    @property
    def info(self) -> Optional[PlayerInfo]:
        return self.auth.player_info

    async def load(self, restore_key: Union[str, SecretStr], device: Optional[DeviceConfig] = None) -> PlayerInfo:
        """Call POST player/load."""
        return await self.auth.load_player(restore_key, device)

    async def get_info(self, player_id: Optional[str] = None) -> Dict[str, Any]:
        """Call POST player/getplayerinfo."""
        payload = {}
        if player_id:
            payload["id"] = player_id

        logger.info("Fetching player info for player_id: %s", player_id or "self")
        resp = await self.client.request("player/getplayerinfo", payload)
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}

    async def fill_potions(self, amount: int = 1) -> Dict[str, Any]:
        """Call POST player/fillpotion."""
        req = FillPotionRequest(amount=amount)
        logger.info("Filling potions amount: %d", amount)
        resp = await self.client.request("player/fillpotion", req)
        data = resp.data if isinstance(resp.data, dict) else {}
        if self.info and "potion" in data:
            self.info.potion = int(data["potion"])
        return data

    async def comeback(self) -> Dict[str, Any]:
        """Call POST player/comeback."""
        logger.info("Calling player/comeback...")
        resp = await self.client.request("player/comeback", {})
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}

    async def get_language_patch(self) -> Dict[str, Any]:
        """Call POST player/languagepatch."""
        logger.info("Fetching language patch...")
        resp = await self.client.request("player/languagepatch", {})
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}
