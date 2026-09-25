"""Tribe information and member listing service."""

import logging
from typing import Any, Dict, List
from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import TribeMember

logger = logging.getLogger("fruitcraft.services.tribe")


class TribeService:
    """Manages tribe actions and member listings."""

    def __init__(self, api_client: FruitCraftAPIClient):
        self.client = api_client

    async def get_members(self) -> List[TribeMember]:
        """Fetch tribe members list (POST tribe/members)."""
        logger.info("Fetching tribe members...")
        resp = await self.client.request("tribe/members", {})

        members = []
        data = resp.data
        raw_list = data if isinstance(data, list) else (data.get("members", []) if isinstance(data, dict) else [])

        for item in raw_list:
            if isinstance(item, dict):
                members.append(
                    TribeMember(
                        id=str(item.get("id", "")),
                        name=str(item.get("name", "")),
                        rank=int(item.get("rank", 0)),
                        xp=int(item.get("xp", 0)),
                        gold=int(item.get("gold", 0)),
                        permission=int(item.get("permission", 0)),
                        level=int(item.get("level", 1)),
                        def_power=int(item.get("def_power", 0)),
                        league=int(item.get("league", 0)),
                        avatar=int(item.get("avatar", 0)),
                        status=str(item.get("status", "active")),
                    )
                )

        logger.info("Found %d tribe members.", len(members))
        return members
