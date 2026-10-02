"""Base worker state machine and lifecycle manager."""

import asyncio
from datetime import datetime, timezone
import logging
import random
from typing import Optional, Dict, Any

from src.fruitcraft_bot.core.events import event_bus
from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.db.database import AsyncSessionLocal
from src.fruitcraft_bot.db.repository import AccountRepository
from src.fruitcraft_bot.services.notification_service import notification_service
import fruitbot.exceptions as fb_exceptions

logger = logging.getLogger(__name__)


class BaseWorker:
    """Abstract base worker implementing state machine and controls."""

    def __init__(self, account_id: str, account_name: str, worker_type: str):
        self.account_id = account_id
        self.account_name = account_name
        self.worker_type = worker_type  # "BattleWorker", "MineWorker", "QuestWorker"

        self.status: str = "STOPPED"    # STOPPED, RUNNING, PAUSED, WAITING, ERROR
        self.started_at: Optional[datetime] = None
        self.last_action: Optional[str] = "None"
        self.next_action: Optional[str] = "Idle"
        self.last_error: Optional[str] = None
        self.action_count: int = 0

        self._task: Optional[asyncio.Task] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Unpaused initially
        self._stop_requested = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize worker state for API and WebSocket."""
        return {
            "worker": self.worker_type,
            "account_id": self.account_id,
            "account": self.account_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_action": self.last_action,
            "next_action": self.next_action,
            "last_error": self.last_error,
            "action_count": self.action_count
        }

    async def _emit_status(self):
        """Emit worker status to WebSockets and DB."""
        await event_bus.publish(
            event_type="WORKER_STATUS",
            account_id=self.account_id,
            account_name=self.account_name,
            message=f"{self.worker_type} is now {self.status}",
            metadata=self.to_dict()
        )

        # Update Account table in DB
        async with AsyncSessionLocal() as session:
            updates = {}
            if self.worker_type == "BattleWorker":
                updates["battle_worker_status"] = self.status
            elif self.worker_type == "MineWorker":
                updates["mine_worker_status"] = self.status
            elif self.worker_type == "QuestWorker":
                updates["quest_worker_status"] = self.status
            updates["next_action"] = self.next_action
            if self.last_error:
                updates["last_error"] = self.last_error
            await AccountRepository.update(session, self.account_id, updates)
            await session.commit()

    async def start(self):
        """Start worker loop."""
        if self.status == "RUNNING":
            return
        self.status = "RUNNING"
        self._stop_requested = False
        self.started_at = datetime.now(timezone.utc)
        self.last_error = None
        self._pause_event.set()
        self._task = asyncio.create_task(self._run_loop())
        await self._emit_status()

    async def stop(self):
        """Stop worker execution."""
        self._stop_requested = True
        self.status = "STOPPED"
        self.next_action = "Stopped"
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._emit_status()

    async def pause(self):
        """Pause worker execution."""
        if self.status == "RUNNING":
            self.status = "PAUSED"
            self._pause_event.clear()
            self.next_action = "Paused by user"
            await self._emit_status()

    async def resume(self):
        """Resume paused worker."""
        if self.status == "PAUSED":
            self.status = "RUNNING"
            self._pause_event.set()
            await self._emit_status()

    async def restart(self):
        """Restart worker."""
        await self.stop()
        await asyncio.sleep(0.5)
        await self.start()

    async def _run_loop(self):
        """Internal execution loop with error handling and auto-restart policy."""
        while not self._stop_requested:
            try:
                # Wait if paused
                await self._pause_event.wait()
                if self._stop_requested:
                    break

                # Execute one unit of work
                await self.execute_step()

            except asyncio.CancelledError:
                break
            except fb_exceptions.CaptchaRequired as e:
                logger.error("Worker %s encountered CAPTCHA: %s", self.worker_type, e)
                self.status = "ERROR"
                self.last_error = "CAPTCHA REQUIRED"
                self.next_action = "Stopped (CAPTCHA)"
                self._stop_requested = True
                await self._emit_status()
                break
            except Exception as e:
                logger.error("Error in %s: %s", self.worker_type, e)
                self.last_error = str(e)
                self.status = "ERROR"
                self.next_action = "Error occurred"
                await self._emit_status()

                if settings.auto_restart_workers and not self._stop_requested:
                    logger.info("Auto-restarting %s in 15 seconds...", self.worker_type)
                    self.status = "WAITING"
                    self.next_action = "Restarting in 15s"
                    await self._emit_status()
                    await asyncio.sleep(15)
                    self.status = "RUNNING"
                else:
                    self._stop_requested = True
                    break

    async def execute_step(self):
        """Subclasses must implement this method."""
        raise NotImplementedError
