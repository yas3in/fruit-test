"""Async Fruitbot Client Wrapper with Proxy Support (Port 10501) and Exception Translation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import urllib3
from urllib3.contrib.socks import SOCKSProxyManager

from fruitbot import Client as FruitbotClient
import fruitbot.exceptions as fb_exceptions
from src.fruitcraft_bot.core.config import settings

logger = logging.getLogger(__name__)


def setup_fruitbot_network(client: FruitbotClient, proxy_url: Optional[str] = None):
    """
    Configures fruitbot's internal urllib3 Network pool to route through proxy
    (such as port 10501) if enabled, with support for HTTP, HTTPS, and SOCKS5.
    """
    if not proxy_url:
        return

    try:
        network_instance = client.sendRequest.__self__
        timeout = settings.api_timeout
        headers = network_instance.headers

        if proxy_url.startswith("socks5://") or proxy_url.startswith("socks5h://"):
            network_instance.http = SOCKSProxyManager(
                proxy_url,
                timeout=timeout,
                headers=headers
            )
            logger.info("Configured fruitbot with SOCKS5 proxy: %s", proxy_url)
        elif proxy_url.startswith("http://") or proxy_url.startswith("https://"):
            network_instance.http = urllib3.ProxyManager(
                proxy_url,
                timeout=timeout,
                headers=headers
            )
            logger.info("Configured fruitbot with HTTP proxy: %s", proxy_url)
    except Exception as e:
        logger.warning("Failed to configure fruitbot proxy manager: %s. Falling back to default network.", e)


class FruitbotClientWrapper:
    """
    Thread-safe, non-blocking asynchronous wrapper around fruitbot.Client.
    Executes blocking fruitbot network requests in worker threads via asyncio.to_thread.
    """

    def __init__(
        self,
        account_id: str,
        restore_key: str,
        proxy_url: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.account_id = account_id
        self.restore_key = restore_key
        self.proxy_url = proxy_url if proxy_url is not None else (settings.proxy_url if settings.proxy_enabled else None)
        self.base_url = base_url or settings.base_url
        self._lock = asyncio.Lock()

        # Ensure persistent session data is reused to avoid Error 124
        import os
        import shutil
        session_file = f"fruit_{account_id}.fb"
        if not os.path.exists(session_file) and os.path.exists("fruit.fb"):
            try:
                shutil.copy("fruit.fb", session_file)
            except Exception:
                pass

        # Initialize underlying fruitbot client
        self.raw_client = FruitbotClient(
            session_name=f"fruit_{account_id}",
            restore_key=restore_key,
            base_url=self.base_url,
            time_out=settings.api_timeout
        )

        # Configure connection proxy if enabled
        if self.proxy_url:
            setup_fruitbot_network(self.raw_client, self.proxy_url)

    async def _execute(self, func, *args, **kwargs) -> Any:
        """Execute a blocking fruitbot call in a thread pool."""
        async with self._lock:
            try:
                return await asyncio.to_thread(func, *args, **kwargs)
            except fb_exceptions.CaptchaRequired as e:
                logger.error("CAPTCHA required for account %s: %s", self.account_id, e)
                raise
            except fb_exceptions.AccountBlocked as e:
                logger.error("Account %s is blocked: %s", self.account_id, e)
                raise
            except Exception as e:
                logger.error("FruitCraft API error on account %s: %s", self.account_id, e)
                raise

    async def load_player(self, save_session: bool = True) -> Dict[str, Any]:
        """Load player profile, stats, cards, and resources."""
        return await self._execute(self.raw_client.loadPlayer, save_session=save_session)

    async def get_opponents(self) -> List[Dict[str, Any]]:
        """Fetch list of potential battle opponents."""
        res = await self._execute(self.raw_client.getOpponents)
        if isinstance(res, list):
            return res
        if isinstance(res, dict):
            return res.get("opponents", res.get("players", []))
        return []

    async def attack_opponent(
        self,
        opponent_id: int,
        card_ids: List[int],
        hero_id: Optional[int] = None,
        attacks_in_today: int = 0
    ) -> Dict[str, Any]:
        """Perform battle attack against an opponent."""
        return await self._execute(
            self.raw_client.attackOpponent,
            opponent_id=opponent_id,
            card_ids=card_ids,
            hero_id=hero_id,
            number_attacks_today=attacks_in_today
        )

    async def collect_mined_gold(self) -> Dict[str, Any]:
        """Collect accumulated gold from gold mine."""
        return await self._execute(self.raw_client.collectMinedGold)

    async def do_quest(
        self,
        card_ids: List[int],
        hero_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute quest with specified cards."""
        return await self._execute(
            self.raw_client.doQuest,
            card_ids=card_ids,
            hero_id=hero_id
        )

    async def get_my_collection(self) -> Dict[str, Any]:
        """Fetch user card collection."""
        return await self._execute(self.raw_client.getMyCollection)

    async def evolve_card(self, sacrifice_card_ids: List[int]) -> Dict[str, Any]:
        """Evolve card using sacrifice cards."""
        return await self._execute(self.raw_client.evolveCard, sacrifice_card_ids=sacrifice_card_ids)

    async def cooloff_card(self, card_id: int) -> Dict[str, Any]:
        """Purchase cooldown reduction for a card."""
        return await self._execute(self.raw_client.cooloffCard, card_id=card_id)

    async def buy_potion(self, amount: Optional[int] = None) -> Dict[str, Any]:
        """Refill potion."""
        return await self._execute(self.raw_client.buyPotion, amount=amount)

    async def potionize_hero(self, amount: int, hero_id: int) -> Dict[str, Any]:
        """Apply potion to hero."""
        return await self._execute(self.raw_client.potionizeHero, amount=amount, base_hero_id=hero_id)

    async def get_global_ranking(self) -> Dict[str, Any]:
        """Get global rankings."""
        return await self._execute(self.raw_client.getGlobalRanking)

    async def get_my_league_ranking(self) -> Dict[str, Any]:
        """Get current league rankings."""
        return await self._execute(self.raw_client.getMyLeagueRanking)

    async def get_captcha(self) -> bytes:
        """Download CAPTCHA image bytes."""
        return await self._execute(self.raw_client.getCaptcha)
