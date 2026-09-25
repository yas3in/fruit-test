"""Authentication service for FruitCraft API."""

import logging
from typing import Any, Dict, Optional, Union
from fruitcraft_bot.config import SecretStr

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import CardModel, PlayerInfo, PlayerLoadRequest
from fruitcraft_bot.config import DeviceConfig

logger = logging.getLogger("fruitcraft.services.auth")


class AuthService:
    """Handles authentication and initial player load."""

    def __init__(self, api_client: FruitCraftAPIClient):
        self.client = api_client
        self.session_data: Dict[str, Any] = {}
        self.q: Optional[str] = None
        self.player_info: Optional[PlayerInfo] = None

    async def load_player(
        self,
        restore_key: Union[str, SecretStr],
        device: Optional[DeviceConfig] = None,
    ) -> PlayerInfo:
        """
        Authenticate account via POST player/load.
        Never logs or exposes restore_key.
        """
        device_cfg = device or DeviceConfig()
        raw_key = restore_key.get_secret_value() if isinstance(restore_key, SecretStr) else restore_key

        req = PlayerLoadRequest(
            game_version=device_cfg.game_version,
            udid=device_cfg.udid,
            os_type=device_cfg.os_type,
            restore_key=raw_key,
            os_version=device_cfg.os_version,
            model=device_cfg.model,
            metrix_uid=device_cfg.metrix_uid,
            appsflyer_uid=device_cfg.appsflyer_uid,
            device_name=device_cfg.device_name,
            store_type=device_cfg.store_type,
        )

        logger.info("Authenticating player/load...")
        resp = await self.client.request("player/load", req)

        data = resp.data if isinstance(resp.data, dict) else {}
        self.session_data = data
        logger.debug("player/load response keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))
        logger.debug("q value captured: %s", repr(data.get('q') if isinstance(data, dict) else None))

        # Extract initial state and q value
        if "q" in data:
            self.q = str(data["q"])

        player_data = data.get("player", data)
        cards_raw = data.get("cards", player_data.get("cards", []))

        cards = []
        if isinstance(cards_raw, dict):
            cards_raw = list(cards_raw.values())

        if isinstance(cards_raw, list):
            for c in cards_raw:
                if isinstance(c, dict):
                    card_id = int(c.get("id", c.get("card_id", 0)))
                    cards.append(
                        CardModel(
                            id=card_id,
                            name=str(c.get("name", "Card")),
                            power=int(c.get("power", c.get("attack", 0))),
                            health=int(c.get("health", c.get("hp", 0))),
                            level=int(c.get("level", 1)),
                            hero_id=c.get("hero_id"),
                            in_cooldown=bool(c.get("in_cooldown", False)),
                        )
                    )

        self.player_info = PlayerInfo(
            id=str(player_data.get("id", "")),
            name=str(player_data.get("name", "")),
            level=int(player_data.get("level", 1)),
            xp=int(player_data.get("xp", 0)),
            gold=int(player_data.get("gold", 0)),
            nectar=int(player_data.get("nectar", 0)),
            potion=int(player_data.get("potion", 0)),
            rank=int(player_data.get("rank", 0)),
            league=int(player_data.get("league", 0)),
            league_rank=int(player_data.get("league_rank", 0)),
            tribe=player_data.get("tribe_name"),
            total_battles=int(player_data.get("battles", 0)),
            won_battles=int(player_data.get("battles_won", 0)),
            lost_battles=int(player_data.get("battles_lost", 0)),
            cards=cards,
            hero_info=data.get("hero", {}),
            mine_info=data.get("mine", {}),
            gold_collection_allowed=bool(data.get("gold_collection_allowed", True)),
            gold_collection_allowed_at=data.get("gold_collection_allowed_at"),
        )

        logger.info("Authenticated successfully as player: %s (ID: %s, Level: %d)", self.player_info.name, self.player_info.id, self.player_info.level)
        return self.player_info
