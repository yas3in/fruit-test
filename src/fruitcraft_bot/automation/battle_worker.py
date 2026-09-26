"""BattleWorker: Automated battles with strategies, limits, and random delays."""

import asyncio
from datetime import datetime, timezone
import logging
import random
from typing import Optional

from src.fruitcraft_bot.automation.base_worker import BaseWorker
from src.fruitcraft_bot.services.battle_service import battle_service
from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class BattleWorker(BaseWorker):
    def __init__(
        self,
        account_id: str,
        account_name: str,
        max_battles: int = 50,
        strategy: str = "highest_power",
        min_gold: int = 1000,
        max_opponent_defense: int = 100000,
        delay_min: float = 3.0,
        delay_max: float = 6.0
    ):
        super().__init__(account_id, account_name, worker_type="BattleWorker")
        self.max_battles = max_battles
        self.strategy = strategy
        self.min_gold = min_gold
        self.max_opponent_defense = max_opponent_defense
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.battles_done = 0

    async def execute_step(self):
        if self.battles_done >= self.max_battles:
            self.status = "STOPPED"
            self.next_action = "Max battles limit reached"
            self._stop_requested = True
            await self._emit_status()
            return

        self.next_action = "Searching opponent & attacking"
        await self._emit_status()

        async with AsyncSessionLocal() as session:
            try:
                res = await battle_service.execute_battle_step(
                    account_id=self.account_id,
                    db=session,
                    max_opponent_defense=self.max_opponent_defense,
                    min_gold=self.min_gold,
                    strategy=self.strategy
                )
                self.battles_done += 1
                self.action_count += 1
                self.last_action = f"Battle {res['result']} vs {res['opponent']} (+{res['gold_earned']:,} Gold)"
                self.last_error = None
            except Exception as e:
                self.last_error = str(e)
                raise

        # Wait random delay
        delay = round(random.uniform(self.delay_min, self.delay_max), 1)
        self.status = "WAITING"
        self.next_action = f"Cooling down for {delay}s"
        await self._emit_status()

        await asyncio.sleep(delay)
        if not self._stop_requested and self.status != "PAUSED":
            self.status = "RUNNING"
