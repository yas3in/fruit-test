"""MineWorker: Automated gold collection with interval scheduling and countdown."""

import asyncio
from datetime import datetime, timezone, timedelta
import logging
from typing import Optional

from src.fruitcraft_bot.automation.base_worker import BaseWorker
from src.fruitcraft_bot.services.mine_service import mine_service
from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class MineWorker(BaseWorker):
    def __init__(
        self,
        account_id: str,
        account_name: str,
        interval_minutes: int = 30
    ):
        super().__init__(account_id, account_name, worker_type="MineWorker")
        self.interval_minutes = interval_minutes

    async def execute_step(self):
        self.next_action = "Collecting mined gold"
        await self._emit_status()

        async with AsyncSessionLocal() as session:
            try:
                res = await mine_service.collect_gold(
                    account_id=self.account_id,
                    db=session
                )
                gold_collected = res.get("gold_collected", 0)
                self.action_count += 1
                self.last_action = f"Collected {gold_collected:,} gold"
                self.last_error = None
            except Exception as e:
                self.last_error = str(e)
                logger.warning("Mine collection error: %s", e)

        # Wait until next collection cycle
        wait_seconds = self.interval_minutes * 60
        self.status = "WAITING"
        self.next_action = f"Next collection in {self.interval_minutes}m"
        await self._emit_status()

        # Sleep in small slices to respond promptly to stop/pause requests
        elapsed = 0
        while elapsed < wait_seconds and not self._stop_requested:
            await self._pause_event.wait()
            await asyncio.sleep(5)
            elapsed += 5

        if not self._stop_requested and self.status != "PAUSED":
            self.status = "RUNNING"
