"""Client pool for managing multi-account Fruitbot instances."""

import asyncio
from typing import Dict, Optional
from src.fruitcraft_bot.fruitbot_wrapper.client import FruitbotClientWrapper


class ClientPool:
    """Singleton pool managing live FruitbotClientWrapper instances per account."""

    def __init__(self):
        self._clients: Dict[str, FruitbotClientWrapper] = {}
        self._lock = asyncio.Lock()

    async def get_client(
        self,
        account_id: str,
        restore_key: str,
        proxy_url: Optional[str] = None
    ) -> FruitbotClientWrapper:
        async with self._lock:
            if account_id in self._clients:
                existing = self._clients[account_id]
                # If restore key changed, re-instantiate
                if existing.restore_key == restore_key:
                    return existing
            wrapper = FruitbotClientWrapper(
                account_id=account_id,
                restore_key=restore_key,
                proxy_url=proxy_url
            )
            self._clients[account_id] = wrapper
            return wrapper

    async def remove_client(self, account_id: str):
        async with self._lock:
            if account_id in self._clients:
                del self._clients[account_id]


client_pool = ClientPool()
