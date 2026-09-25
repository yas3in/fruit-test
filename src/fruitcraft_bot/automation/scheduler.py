"""Multi-account worker scheduler and lifecycle manager."""

import asyncio
import logging
from typing import Dict, List, Optional

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.automation.battle_worker import BattleWorker
from fruitcraft_bot.automation.mine_worker import MineWorker
from fruitcraft_bot.automation.quest_worker import QuestWorker
from fruitcraft_bot.config import AccountConfig
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.battle import BattleService
from fruitcraft_bot.services.cards import CardService
from fruitcraft_bot.services.mine import MineService
from fruitcraft_bot.services.player import PlayerService
from fruitcraft_bot.services.quest import QuestService
from fruitcraft_bot.storage.state import StateDatabase

logger = logging.getLogger("fruitcraft.automation.scheduler")


class AccountContainer:
    """Isolated container per account ensuring zero shared state."""

    def __init__(self, config: AccountConfig, db: StateDatabase):
        self.config = config
        self.db = db

        # Independent HTTP client & Services
        self.client = FruitCraftAPIClient(
            passport=config.passport.get_secret_value() if config.passport else None,
            user_agent=f"Dalvik/2.1.0 (Linux; U; Android {config.device.os_version}; {config.device.model})"
        )
        self.auth = AuthService(self.client)
        self.player = PlayerService(self.client, self.auth)
        self.battle = BattleService(self.client, self.auth)
        self.quest = QuestService(self.client, self.auth)
        self.cards = CardService(self.client, self.auth)
        self.mine = MineService(self.client, self.auth, self.cards)

        # Workers
        self.battle_worker = BattleWorker(self.config, self.auth, self.player, self.battle, self.cards, self.db)
        self.quest_worker = QuestWorker(self.config, self.auth, self.quest, self.cards, self.db)
        self.mine_worker = MineWorker(self.config, self.auth, self.mine, self.db)

        self.tasks: List[asyncio.Task] = []

    async def close(self):
        """Clean up tasks and HTTP connections."""
        for worker in (self.battle_worker, self.quest_worker, self.mine_worker):
            worker.stop()
        for task in self.tasks:
            if not task.done():
                task.cancel()
        await self.client.close()


class Scheduler:
    """Manages worker loops across single or multiple accounts."""

    def __init__(self, accounts: Dict[str, AccountConfig], db_path: str = "fruitcraft.db"):
        self.accounts_config = accounts
        self.db = StateDatabase(db_path)
        self.containers: Dict[str, AccountContainer] = {}

    def _init_containers(self):
        for acc_id, cfg in self.accounts_config.items():
            if acc_id not in self.containers:
                self.containers[acc_id] = AccountContainer(cfg, self.db)

    async def start(self):
        """Launch configured workers for all accounts concurrently."""
        self._init_containers()
        all_tasks = []

        for acc_id, container in self.containers.items():
            logger.info("Starting automation workers for account: %s", acc_id)
            cfg = container.config.automation

            if cfg.battle_enabled:
                t_battle = asyncio.create_task(container.battle_worker.run())
                container.tasks.append(t_battle)
                all_tasks.append(t_battle)

            if cfg.quest_enabled:
                t_quest = asyncio.create_task(container.quest_worker.run())
                container.tasks.append(t_quest)
                all_tasks.append(t_quest)

            if cfg.mine_enabled:
                t_mine = asyncio.create_task(container.mine_worker.run())
                container.tasks.append(t_mine)
                all_tasks.append(t_mine)

        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)

    async def stop(self):
        """Stop all running account workers."""
        logger.info("Stopping scheduler...")
        for container in self.containers.values():
            await container.close()
