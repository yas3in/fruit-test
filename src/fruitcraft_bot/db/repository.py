"""Repository layer for database operations."""

from datetime import datetime, timezone, date
import json
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func, desc, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from src.fruitcraft_bot.db.models import (
    Account, BattleRecord, QuestRecord, MineCollectionRecord,
    ActivityLog, NotificationRecord, SystemSetting, DailyReport
)


class AccountRepository:
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Account]:
        stmt = select(Account).order_by(Account.created_at.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, account_id: str) -> Optional[Account]:
        stmt = select(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, account: Account) -> Account:
        session.add(account)
        await session.flush()
        return account

    @staticmethod
    async def update(session: AsyncSession, account_id: str, updates: Dict[str, Any]) -> Optional[Account]:
        updates["updated_at"] = datetime.now(timezone.utc)
        stmt = (
            update(Account)
            .where(Account.id == account_id)
            .values(**updates)
            .execution_options(synchronize_session="fetch")
        )
        await session.execute(stmt)
        await session.flush()
        return await AccountRepository.get_by_id(session, account_id)

    @staticmethod
    async def delete(session: AsyncSession, account_id: str) -> bool:
        stmt = delete(Account).where(Account.id == account_id)
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount > 0


class BattleRepository:
    @staticmethod
    async def add(session: AsyncSession, battle: BattleRecord) -> BattleRecord:
        session.add(battle)
        await session.flush()
        return battle

    @staticmethod
    async def get_recent(session: AsyncSession, account_id: str, limit: int = 20) -> List[BattleRecord]:
        stmt = (
            select(BattleRecord)
            .where(BattleRecord.account_id == account_id)
            .order_by(BattleRecord.timestamp.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_today_stats(session: AsyncSession, account_id: str) -> Dict[str, Any]:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(
            func.count(BattleRecord.id).label("total"),
            func.sum(case((BattleRecord.result == "WIN", 1), else_=0)).label("wins"),
            func.sum(case((BattleRecord.result == "LOSS", 1), else_=0)).label("losses"),
            func.coalesce(func.sum(BattleRecord.gold_earned), 0).label("gold_earned"),
            func.coalesce(func.sum(BattleRecord.xp_earned), 0).label("xp_earned")
        ).where(
            and_(
                BattleRecord.account_id == account_id,
                BattleRecord.timestamp >= today_start
            )
        )
        result = await session.execute(stmt)
        row = result.fetchone()
        total = row.total or 0
        wins = row.wins or 0
        losses = row.losses or 0
        win_rate = round((wins / total * 100), 1) if total > 0 else 0.0
        return {
            "total_battles_today": total,
            "wins_today": wins,
            "losses_today": losses,
            "win_rate_today": win_rate,
            "gold_earned_today": row.gold_earned or 0,
            "xp_earned_today": row.xp_earned or 0
        }


class QuestRepository:
    @staticmethod
    async def add(session: AsyncSession, quest: QuestRecord) -> QuestRecord:
        session.add(quest)
        await session.flush()
        return quest

    @staticmethod
    async def get_today_stats(session: AsyncSession, account_id: str) -> Dict[str, Any]:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(
            func.count(QuestRecord.id).label("total"),
            func.coalesce(func.sum(QuestRecord.gold_earned), 0).label("gold_earned"),
            func.coalesce(func.sum(QuestRecord.xp_earned), 0).label("xp_earned")
        ).where(
            and_(
                QuestRecord.account_id == account_id,
                QuestRecord.timestamp >= today_start
            )
        )
        result = await session.execute(stmt)
        row = result.fetchone()
        return {
            "quests_today": row.total or 0,
            "gold_earned_today": row.gold_earned or 0,
            "xp_earned_today": row.xp_earned or 0
        }

    @staticmethod
    async def get_recent(session: AsyncSession, account_id: str, limit: int = 15) -> List[QuestRecord]:
        stmt = (
            select(QuestRecord)
            .where(QuestRecord.account_id == account_id)
            .order_by(QuestRecord.timestamp.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


class MineRepository:
    @staticmethod
    async def add(session: AsyncSession, record: MineCollectionRecord) -> MineCollectionRecord:
        session.add(record)
        await session.flush()
        return record

    @staticmethod
    async def get_today_stats(session: AsyncSession, account_id: str) -> Dict[str, Any]:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(
            func.count(MineCollectionRecord.id).label("total_collections"),
            func.coalesce(func.sum(MineCollectionRecord.gold_collected), 0).label("gold_collected"),
            func.max(MineCollectionRecord.timestamp).label("last_collection")
        ).where(
            and_(
                MineCollectionRecord.account_id == account_id,
                MineCollectionRecord.timestamp >= today_start
            )
        )
        result = await session.execute(stmt)
        row = result.fetchone()
        return {
            "collections_today": row.total_collections or 0,
            "gold_collected_today": row.gold_collected or 0,
            "last_collection_time": row.last_collection.isoformat() if row.last_collection else None
        }


class ActivityRepository:
    @staticmethod
    async def add(session: AsyncSession, activity: ActivityLog) -> ActivityLog:
        session.add(activity)
        await session.flush()
        return activity

    @staticmethod
    async def get_recent(
        session: AsyncSession,
        limit: int = 50,
        account_id: Optional[str] = None
    ) -> List[ActivityLog]:
        stmt = select(ActivityLog)
        if account_id:
            stmt = stmt.where(ActivityLog.account_id == account_id)
        stmt = stmt.order_by(ActivityLog.timestamp.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())


class NotificationRepository:
    @staticmethod
    async def add_or_deduplicate(
        session: AsyncSession,
        title: str,
        message: str,
        priority: str = "INFO",
        deduplication_key: Optional[str] = None,
        account_id: Optional[str] = None,
        account_name: str = "System"
    ) -> NotificationRecord:
        now = datetime.now(timezone.utc)
        if deduplication_key:
            # Check if there is an existing notification with this deduplication_key
            stmt = (
                select(NotificationRecord)
                .where(NotificationRecord.deduplication_key == deduplication_key)
                .order_by(NotificationRecord.timestamp.desc())
                .limit(1)
            )
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                existing.occurrence_count += 1
                existing.last_occurrence = now
                existing.message = message
                existing.is_read = False
                await session.flush()
                return existing

        notif = NotificationRecord(
            account_id=account_id,
            account_name=account_name,
            timestamp=now,
            priority=priority,
            title=title,
            message=message,
            deduplication_key=deduplication_key,
            occurrence_count=1,
            last_occurrence=now,
            is_read=False
        )
        session.add(notif)
        await session.flush()
        return notif

    @staticmethod
    async def get_recent(
        session: AsyncSession,
        limit: int = 50,
        priority: Optional[str] = None
    ) -> List[NotificationRecord]:
        stmt = select(NotificationRecord)
        if priority:
            stmt = stmt.where(NotificationRecord.priority == priority)
        stmt = stmt.order_by(NotificationRecord.last_occurrence.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())


class SettingsRepository:
    @staticmethod
    async def get(session: AsyncSession, key: str, default: Any = None) -> Any:
        stmt = select(SystemSetting).where(SystemSetting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            try:
                return json.loads(setting.value)
            except Exception:
                return setting.value
        return default

    @staticmethod
    async def set(session: AsyncSession, key: str, value: Any) -> None:
        serialized = json.dumps(value) if not isinstance(value, str) else value
        stmt = select(SystemSetting).where(SystemSetting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = serialized
            setting.updated_at = datetime.now(timezone.utc)
        else:
            session.add(SystemSetting(key=key, value=serialized))
        await session.flush()
