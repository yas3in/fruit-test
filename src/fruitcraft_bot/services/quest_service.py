"""Quest operations and quest tracking service."""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.repository import AccountRepository, QuestRepository, ActivityRepository
from src.fruitcraft_bot.db.models import QuestRecord, ActivityLog
from src.fruitcraft_bot.fruitbot_wrapper.pool import client_pool
from src.fruitcraft_bot.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class QuestService:
    @staticmethod
    async def get_quest_info(account_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Aggregate quest status for the Quests page."""
        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            return {}

        today_stats = await QuestRepository.get_today_stats(db, account_id)
        recent_quests = await QuestRepository.get_recent(db, account_id, limit=1)
        last_quest = recent_quests[0] if recent_quests else None

        return {
            "account_id": account.id,
            "account_name": account.name,
            "quests_completed_today": today_stats.get("quests_today", 0),
            "current_quest": "Daily Adventure" if account.quest_worker_status == "RUNNING" else "Idle",
            "last_quest_result": last_quest.result if last_quest else "None",
            "gold_earned": today_stats.get("gold_earned_today", 0),
            "xp_earned": today_stats.get("xp_earned_today", 0),
            "worker_status": account.quest_worker_status or "STOPPED"
        }

    @staticmethod
    async def execute_quest_step(account_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Execute quest via FruitCraft API and update records."""
        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found.")

        client = await client_pool.get_client(account.id, account.restore_key)

        # Load player data and select exactly 1 weakest card using 10-card fallback rotation
        from src.fruitcraft_bot.bot_actions import parse_cards_list, get_sorted_weakest_cards, is_card_ready

        player_data = await client.load_player()
        cards_list = parse_cards_list(player_data)
        candidates = get_sorted_weakest_cards(cards_list, limit=10)
        if not candidates:
            raise ValueError("No cards found in player collection.")

        selected_card = None
        for candidate in candidates:
            if is_card_ready(candidate):
                selected_card = candidate
                break

        if not selected_card:
            raise ValueError("All 10 weakest cards are currently in cooldown.")

        quest_cards = [selected_card["id"]]
        res = await client.do_quest(card_ids=quest_cards)

        gold_earned = int(res.get("gold", res.get("gold_earned", 0)))
        xp_earned = int(res.get("xp", res.get("xp_earned", 0)))
        now = datetime.now(timezone.utc)

        # Record to DB
        record = QuestRecord(
            account_id=account.id,
            timestamp=now,
            quest_name="Standard Quest",
            result="SUCCESS",
            gold_earned=gold_earned,
            xp_earned=xp_earned,
            cards_used=json.dumps(quest_cards)
        )
        await QuestRepository.add(db, record)

        # Activity log
        await ActivityRepository.add(db, ActivityLog(
            account_id=account.id,
            account_name=account.name,
            event_type="QUEST_COMPLETED",
            message=f"Completed quest: +{gold_earned:,} Gold, +{xp_earned:,} XP"
        ))

        # Notification
        await notification_service.notify(
            db=db,
            title="Quest Completed",
            message=f"{account.name} completed quest (+{gold_earned:,} Gold, +{xp_earned:,} XP)",
            priority="INFO",
            event_type="QUEST_FINISHED",
            account_id=account.id,
            account_name=account.name,
            metadata={"gold_earned": gold_earned, "xp_earned": xp_earned}
        )

        return {
            "result": "SUCCESS",
            "gold_earned": gold_earned,
            "xp_earned": xp_earned
        }


quest_service = QuestService()
