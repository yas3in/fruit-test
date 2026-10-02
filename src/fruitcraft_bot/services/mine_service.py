"""Gold mine management and collection service."""

from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.repository import AccountRepository, MineRepository, ActivityRepository
from src.fruitcraft_bot.db.models import MineCollectionRecord, ActivityLog
from src.fruitcraft_bot.fruitbot_wrapper.pool import client_pool
from src.fruitcraft_bot.services.notification_service import notification_service
from src.fruitcraft_bot.core.config import settings

logger = logging.getLogger(__name__)


class MineService:
    @staticmethod
    async def get_mine_info(account_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Aggregate mine status for the Mine page."""
        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            return {}

        today_stats = await MineRepository.get_today_stats(db, account_id)

        # Estimate next collection time based on last collection or configured delay
        next_collection_dt = datetime.now(timezone.utc) + timedelta(minutes=settings.mine_delay_minutes)
        last_col = today_stats.get("last_collection_time")
        if last_col:
            try:
                last_dt = datetime.fromisoformat(last_col)
                scheduled_next = last_dt + timedelta(minutes=settings.mine_delay_minutes)
                if scheduled_next > datetime.now(timezone.utc):
                    next_collection_dt = scheduled_next
            except Exception:
                pass

        diff_seconds = max(0, int((next_collection_dt - datetime.now(timezone.utc)).total_seconds()))
        hours, remainder = divmod(diff_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        from src.fruitcraft_bot.automation.worker_manager import worker_manager
        worker = worker_manager._workers.get(account_id, {}).get("mine")
        worker_status = worker.status if worker else (account.mine_worker_status or "STOPPED")

        return {
            "account_id": account.id,
            "account_name": account.name,
            "current_gold": account.gold,
            "collection_status": "Ready" if diff_seconds == 0 else "Accumulating",
            "next_collection_time": next_collection_dt.isoformat(),
            "countdown": countdown_str,
            "seconds_remaining": diff_seconds,
            "last_collection_time": last_col or "Never",
            "gold_collected_today": today_stats.get("gold_collected_today", 0),
            "number_of_collections": today_stats.get("collections_today", 0),
            "mine_power": max(100, account.level * 150),
            "mine_capacity": max(50000, account.level * 25000),
            "worker_state": worker_status,
            "worker_status": worker_status
        }

    @staticmethod
    async def collect_gold(account_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Execute gold mine collection via FruitCraft API."""
        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found.")

        client = await client_pool.get_client(account.id, account.restore_key)
        res = await client.collect_mined_gold()

        gold_collected = int(res.get("gold", res.get("gold_collected", 0)))
        now = datetime.now(timezone.utc)

        # Record collection
        record = MineCollectionRecord(
            account_id=account.id,
            timestamp=now,
            gold_collected=gold_collected
        )
        await MineRepository.add(db, record)

        # Update account gold if returned
        if "player" in res and "gold" in res["player"]:
            await AccountRepository.update(db, account.id, {"gold": res["player"]["gold"], "last_error": None})
        else:
            await AccountRepository.update(db, account.id, {"gold": account.gold + gold_collected, "last_error": None})

        # Activity log
        await ActivityRepository.add(db, ActivityLog(
            account_id=account.id,
            account_name=account.name,
            event_type="GOLD_COLLECTED",
            message=f"Collected {gold_collected:,} gold from mine."
        ))

        # Notification
        await notification_service.notify(
            db=db,
            title="Gold Collected",
            message=f"{account.name} collected {gold_collected:,} gold from mine.",
            priority="INFO",
            event_type="GOLD_COLLECTED",
            account_id=account.id,
            account_name=account.name,
            metadata={"gold_collected": gold_collected}
        )
        await db.commit()

        return {
            "status": "success",
            "gold_collected": gold_collected
        }


mine_service = MineService()
