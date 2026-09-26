"""Worker manager and supervisor for all account automation workers."""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from src.fruitcraft_bot.automation.battle_worker import BattleWorker
from src.fruitcraft_bot.automation.mine_worker import MineWorker
from src.fruitcraft_bot.automation.quest_worker import QuestWorker
from src.fruitcraft_bot.automation.base_worker import BaseWorker
from src.fruitcraft_bot.db.database import AsyncSessionLocal
from src.fruitcraft_bot.db.repository import AccountRepository

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages creation, lifecycle, and status reporting of Battle, Mine, and Quest workers."""

    def __init__(self):
        # account_id -> { "battle": BattleWorker, "mine": MineWorker, "quest": QuestWorker }
        self._workers: Dict[str, Dict[str, BaseWorker]] = {}
        self._lock = asyncio.Lock()

    async def _get_or_create_worker(
        self,
        account_id: str,
        worker_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseWorker:
        async with self._lock:
            if account_id not in self._workers:
                self._workers[account_id] = {}

            type_key = worker_type.lower().replace("worker", "")
            if type_key in self._workers[account_id]:
                return self._workers[account_id][type_key]

            # Fetch account name
            account_name = f"Account {account_id}"
            async with AsyncSessionLocal() as session:
                acc = await AccountRepository.get_by_id(session, account_id)
                if acc:
                    account_name = acc.name

            conf = config or {}
            worker: BaseWorker
            if type_key == "battle":
                worker = BattleWorker(
                    account_id=account_id,
                    account_name=account_name,
                    max_battles=conf.get("max_battles", 50),
                    strategy=conf.get("strategy", "highest_power"),
                    min_gold=conf.get("min_gold", 1000),
                    max_opponent_defense=conf.get("max_opponent_defense", 100000),
                    delay_min=conf.get("delay_min", 3.0),
                    delay_max=conf.get("delay_max", 6.0)
                )
            elif type_key == "mine":
                worker = MineWorker(
                    account_id=account_id,
                    account_name=account_name,
                    interval_minutes=conf.get("interval_minutes", 30)
                )
            elif type_key == "quest":
                worker = QuestWorker(
                    account_id=account_id,
                    account_name=account_name,
                    max_quests=conf.get("max_quests", 30),
                    delay_min=conf.get("delay_min", 4.0),
                    delay_max=conf.get("delay_max", 8.0)
                )
            else:
                raise ValueError(f"Unknown worker type: {worker_type}")

            self._workers[account_id][type_key] = worker
            return worker

    async def get_all_workers(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return status list for all registered workers."""
        async with self._lock:
            # First, ensure all accounts in DB have placeholders
            async with AsyncSessionLocal() as session:
                accounts = await AccountRepository.get_all(session)
                for acc in accounts:
                    if acc.id not in self._workers:
                        self._workers[acc.id] = {
                            "battle": BattleWorker(acc.id, acc.name),
                            "mine": MineWorker(acc.id, acc.name),
                            "quest": QuestWorker(acc.id, acc.name)
                        }

            res = []
            for acc_id, type_dict in self._workers.items():
                if account_id and acc_id != account_id:
                    continue
                for w in type_dict.values():
                    res.append(w.to_dict())
            return res

    async def start_worker(self, account_id: str, worker_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        worker = await self._get_or_create_worker(account_id, worker_type, config)
        await worker.start()
        return worker.to_dict()

    async def stop_worker(self, account_id: str, worker_type: str) -> Dict[str, Any]:
        worker = await self._get_or_create_worker(account_id, worker_type)
        await worker.stop()
        return worker.to_dict()

    async def pause_worker(self, account_id: str, worker_type: str) -> Dict[str, Any]:
        worker = await self._get_or_create_worker(account_id, worker_type)
        await worker.pause()
        return worker.to_dict()

    async def resume_worker(self, account_id: str, worker_type: str) -> Dict[str, Any]:
        worker = await self._get_or_create_worker(account_id, worker_type)
        await worker.resume()
        return worker.to_dict()

    async def restart_worker(self, account_id: str, worker_type: str) -> Dict[str, Any]:
        worker = await self._get_or_create_worker(account_id, worker_type)
        await worker.restart()
        return worker.to_dict()

    async def stop_all_for_account(self, account_id: str):
        async with self._lock:
            if account_id in self._workers:
                for w in self._workers[account_id].values():
                    await w.stop()


worker_manager = WorkerManager()
