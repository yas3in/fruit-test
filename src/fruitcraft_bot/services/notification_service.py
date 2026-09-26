"""Notification service with deduplication, priority management, and event dispatch."""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.core.events import event_bus
from src.fruitcraft_bot.db.repository import NotificationRepository
from src.fruitcraft_bot.services.telegram_service import telegram_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles notification generation, deduplication, and multi-channel dispatch."""

    def __init__(self):
        self._dedup_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def notify(
        self,
        db: AsyncSession,
        title: str,
        message: str,
        priority: str = "INFO",  # INFO, WARNING, ERROR, CRITICAL
        event_type: str = "SYSTEM_NOTIFICATION",
        account_id: Optional[str] = None,
        account_name: str = "System",
        deduplication_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        send_telegram: bool = True
    ):
        """Create notification with deduplication, DB persistence, WebSocket broadcast, and Telegram alert."""
        priority = priority.upper()
        now = datetime.now(timezone.utc)

        # 1. Deduplication logic (Section 56)
        is_repeated = False
        repeated_count = 1
        if deduplication_key:
            async with self._lock:
                if deduplication_key in self._dedup_cache:
                    cached = self._dedup_cache[deduplication_key]
                    cached["count"] += 1
                    cached["last_time"] = now
                    repeated_count = cached["count"]
                    is_repeated = True
                else:
                    self._dedup_cache[deduplication_key] = {
                        "count": 1,
                        "first_time": now,
                        "last_time": now
                    }

        # 2. Persist in database
        try:
            record = await NotificationRepository.add_or_deduplicate(
                session=db,
                title=title,
                message=message,
                priority=priority,
                deduplication_key=deduplication_key,
                account_id=account_id,
                account_name=account_name
            )
            repeated_count = record.occurrence_count
        except Exception as e:
            logger.warning("Could not persist notification in DB: %s", e)

        # 3. Publish to WebSocket dashboard (Section 51)
        await event_bus.publish(
            event_type=event_type,
            account_id=account_id,
            account_name=account_name,
            message=message,
            metadata={
                "priority": priority,
                "title": title,
                "repeated_count": repeated_count,
                **(metadata or {})
            },
            priority=priority
        )

        # 4. Dispatch to Telegram (Section 48, 55, 56)
        if send_telegram and telegram_service.enabled:
            try:
                if priority == "CRITICAL" and "CAPTCHA" in title.upper():
                    await telegram_service.send_captcha_alert(account_name)
                elif priority in ("ERROR", "CRITICAL"):
                    # Deduplicated error report to avoid Telegram spam
                    if not is_repeated or repeated_count in (5, 10, 25, 50, 100):
                        await telegram_service.send_error(
                            account_name=account_name,
                            endpoint=metadata.get("endpoint", "API") if metadata else "API",
                            error_message=message,
                            repeated_failures=repeated_count
                        )
                elif priority == "INFO" and event_type == "BATTLE_FINISHED":
                    meta = metadata or {}
                    await telegram_service.send_battle_result(
                        account_name=account_name,
                        opponent_name=meta.get("opponent_name", "Unknown"),
                        result=meta.get("result", "WIN"),
                        gold_earned=meta.get("gold_earned", 0),
                        xp_earned=meta.get("xp_earned", 0)
                    )
                elif priority == "INFO" and "WORKER" in event_type:
                    meta = metadata or {}
                    await telegram_service.send_worker_status(
                        account_name=account_name,
                        worker_name=meta.get("worker_name", "Worker"),
                        status=meta.get("status", "UPDATED"),
                        details=message
                    )
            except Exception as e:
                logger.error("Error dispatching notification to Telegram: %s", e)


notification_service = NotificationService()
