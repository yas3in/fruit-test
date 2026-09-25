"""Mine collection worker using server-calculated timing."""

import asyncio
import logging
import time
from typing import Optional

from fruitcraft_bot.api.errors import CaptchaRequiredError, FruitCraftError
from fruitcraft_bot.config import AccountConfig
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.mine import MineService
from fruitcraft_bot.storage.state import StateDatabase

logger = logging.getLogger("fruitcraft.automation.mine")


class MineWorker:
    """Automated mine collection worker using server-allowed schedule."""

    def __init__(
        self,
        account_config: AccountConfig,
        auth_service: AuthService,
        mine_service: MineService,
        db: Optional[StateDatabase] = None,
    ):
        self.config = account_config
        self.auto_cfg = account_config.automation
        self.auth = auth_service
        self.mine = mine_service
        self.db = db or StateDatabase()
        self._running = False
        self.total_collected = 0

    def stop(self):
        self._running = False

    async def run(self):
        """Execute mine worker loop."""
        self._running = True

        if not self.auth.player_info:
            try:
                await self.auth.load_player(self.config.restore_key, self.config.device)
            except Exception as e:
                logger.error("[%s] Auth failed in mine worker: %s", self.config.account_id, e)
                return

        while self._running:
            try:
                # 1. Evaluate current mine collection status
                status = self.mine.get_status()

                if status.allowed:
                    logger.info("[%s] Gold collection allowed. Collecting now...", self.config.account_id)
                    res = await self.mine.collect()
                    self.total_collected += res.collected_gold
                    self.db.record_gold_collection(
                        account_id=self.config.account_id,
                        collected=res.collected_gold,
                        player_gold=res.player_gold,
                    )

                    if res.needs_captcha:
                        logger.warning("[%s] CAPTCHA required during mine collection. Stopping.", self.config.account_id)
                        self._running = False
                        break

                    # Re-evaluate status after collection
                    status = self.mine.get_status()

                # 2. Calculate sleep interval until next allowed time
                wait_seconds = max(5.0, status.seconds_until_next)
                logger.info("[%s] Mine next collection ready in %.1fs (allowed_at=%s). Sleeping...", self.config.account_id, wait_seconds, status.next_allowed_at)

                # Sleep in short increments to allow graceful cancellation
                slept = 0.0
                step = 2.0
                while self._running and slept < wait_seconds:
                    await asyncio.sleep(min(step, wait_seconds - slept))
                    slept += step

            except CaptchaRequiredError:
                logger.warning("[%s] CAPTCHA required in mine worker. Halting.", self.config.account_id)
                self._running = False
                break

            except FruitCraftError as e:
                self.db.record_error(self.config.account_id, e.endpoint or "mine", e.code or 0, e.message)
                if self.auto_cfg.stop_on_error:
                    self._running = False
                    break
                await asyncio.sleep(10.0)

            except Exception as e:
                logger.error("[%s] Error in mine worker: %s", self.config.account_id, e)
                self._running = False
                break

        logger.info("[%s] Mine worker stopped. Total gold collected: %d", self.config.account_id, self.total_collected)
