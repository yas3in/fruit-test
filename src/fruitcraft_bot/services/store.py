"""Experimental store service for FruitCraft."""

import logging
from typing import Any, Dict, Optional
from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import BuyCardPackRequest

logger = logging.getLogger("fruitcraft.services.store")


class StoreService:
    """Isolated experimental service for store operations."""

    def __init__(self, api_client: FruitCraftAPIClient, experimental_enabled: bool = False):
        self.client = api_client
        self.experimental_enabled = experimental_enabled

    async def buy_card_pack(
        self,
        pack_id: int = 1,
        currency: str = "gold",
        custom_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Experimental endpoint: POST store/buycardpack.
        Requires experimental_enabled=True.
        """
        if not self.experimental_enabled:
            raise RuntimeError(
                "Store operations are experimental and not present in standard public specs. "
                "Set experimental_enabled=True to enable."
            )

        payload = custom_payload or BuyCardPackRequest(pack_id=pack_id, currency=currency).model_dump()
        logger.warning("[EXPERIMENTAL] Purchasing card pack via store/buycardpack...")
        resp = await self.client.request("store/buycardpack", payload)
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}
