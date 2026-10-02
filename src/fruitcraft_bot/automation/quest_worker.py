"""QuestWorker: Automated quest execution with delay ranges and quest count limits."""

import asyncio
import logging
import random
from typing import Optional

from src.fruitcraft_bot.automation.base_worker import BaseWorker
from src.fruitcraft_bot.services.quest_service import quest_service
from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class QuestWorker(BaseWorker):
    def __init__(
        self,
        account_id: str,
        account_name: str,
        max_quests: int = 30,
        delay_min: float = 8.0,
        delay_max: float = 8.0
    ):
        super().__init__(account_id, account_name, worker_type="QuestWorker")
        self.max_quests = max_quests
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.quests_done = 0

    async def execute_step(self):
        if self.quests_done >= self.max_quests:
            self.status = "STOPPED"
            self.next_action = "Max quests limit reached"
            self._stop_requested = True
            await self._emit_status()
            return

        self.next_action = "Selecting cards & executing quest"
        await self._emit_status()

        async with AsyncSessionLocal() as session:
            try:
                res = await quest_service.execute_quest_step(
                    account_id=self.account_id,
                    db=session
                )
                self.quests_done += 1
                self.action_count += 1
                self.last_action = f"Quest completed: +{res['gold_earned']:,} Gold, +{res['xp_earned']:,} XP"
                self.last_error = None
            except Exception as e:
                self.last_error = str(e)
                raise

        # Wait random delay
        delay = round(random.uniform(self.delay_min, self.delay_max), 1)
        self.status = "WAITING"
        self.next_action = f"Waiting for next quest in {delay}s"
        await self._emit_status()

        await asyncio.sleep(delay)
        if not self._stop_requested and self.status != "PAUSED":
            self.status = "RUNNING"
