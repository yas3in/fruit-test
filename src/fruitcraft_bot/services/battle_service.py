"""Battle operations, opponent evaluation, and battle logging."""

import json
import logging
from datetime import datetime, timezone
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.repository import AccountRepository, BattleRepository, ActivityRepository
from src.fruitcraft_bot.db.models import BattleRecord, ActivityLog
from src.fruitcraft_bot.fruitbot_wrapper.pool import client_pool
from src.fruitcraft_bot.services.notification_service import notification_service
import fruitbot.exceptions as fb_exceptions

logger = logging.getLogger(__name__)


class BattleService:
    @staticmethod
    async def get_battle_summary(account_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Aggregate battle statistics for the Battle page."""
        today_stats = await BattleRepository.get_today_stats(db, account_id)
        recent_battles = await BattleRepository.get_recent(db, account_id, limit=20)

        # Format recent battles table
        formatted_history = []
        for b in recent_battles:
            cards_used = []
            try:
                cards_used = json.loads(b.cards_used) if b.cards_used else []
            except Exception:
                pass
            formatted_history.append({
                "id": b.id,
                "time": b.timestamp.strftime("%Y-%m-%d %H:%M:%S") if b.timestamp else "",
                "opponent": b.opponent_name,
                "opponent_power": b.opponent_power,
                "result": b.result,
                "gold": b.gold_earned,
                "xp": b.xp_earned,
                "cards": cards_used,
                "duration": f"{b.duration_ms}ms" if b.duration_ms else "N/A"
            })

        account = await AccountRepository.get_by_id(db, account_id)
        from src.fruitcraft_bot.automation.worker_manager import worker_manager
        worker = worker_manager._workers.get(account_id, {}).get("battle")
        worker_status = worker.status if worker else (account.battle_worker_status if account else "STOPPED")

        return {
            **today_stats,
            "recent_battles": formatted_history,
            "worker_status": worker_status,
            "worker_state": worker_status
        }

    @staticmethod
    async def execute_battle_step(
        account_id: str,
        db: AsyncSession,
        max_opponent_defense: int = 100000,
        min_gold: int = 1000,
        strategy: str = "highest_power"
    ) -> Dict[str, Any]:
        """
        Execute a single battle step:
        1. Find best usable cards.
        2. Query opponents.
        3. Select target based on defense/gold criteria.
        4. Attack opponent.
        5. Record battle result and notify.
        """
        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        client = await client_pool.get_client(account.id, account.restore_key)

        # 1. Load player collection to get usable cards
        player_data = await client.load_player()
        cards_raw = player_data.get("cards", [])
        if isinstance(cards_raw, dict):
            cards_list = list(cards_raw.values())
        elif isinstance(cards_raw, list):
            cards_list = cards_raw
        else:
            cards_list = []

        # Filter out cards on cooldown
        usable_cards = []
        for c in cards_list:
            if isinstance(c, dict):
                cid = c.get("id", c.get("card_id"))
                if cid and not c.get("in_cooldown", False):
                    usable_cards.append({
                        "id": int(cid),
                        "power": int(c.get("power", c.get("attack", 0)))
                    })

        if not usable_cards:
            return {
                "result": "WAITING_CARDS",
                "opponent": "None",
                "gold_earned": 0,
                "xp_earned": 0,
                "message": "All cards are in cooldown for battle."
            }

        usable_cards.sort(key=lambda x: x["power"], reverse=True)
        battle_card_ids = [c["id"] for c in usable_cards[:4]]

        # 2. Get opponents
        opponents = await client.get_opponents()
        if not opponents:
            raise ValueError("No opponents found in battle search.")

        # 3. Filter opponent
        target = None
        for opp in opponents:
            opp_def = int(opp.get("defense", opp.get("power", 0)))
            opp_gold = int(opp.get("gold", 0))
            if opp_def <= max_opponent_defense and opp_gold >= min_gold:
                target = opp
                break
        if not target:
            target = opponents[0]

        target_id = int(target.get("id", target.get("player_id")))
        target_name = target.get("name", f"Player #{target_id}")
        target_defense = int(target.get("defense", target.get("power", 0)))

        # 4. Attack
        start_time = time.time()
        res = await client.attack_opponent(
            opponent_id=target_id,
            card_ids=battle_card_ids
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Parse outcome
        # fruitbot attack response usually contains "winner" or "battle"
        battle_info = res.get("battle", res)
        winner_id = battle_info.get("winner_id", res.get("winner"))
        user_id = player_data.get("id")
        result_str = "WIN" if winner_id == user_id or res.get("status") is True else "LOSS"

        gold_earned = int(battle_info.get("gold", res.get("gold_earned", 0)))
        xp_earned = int(battle_info.get("xp", res.get("xp_earned", 0)))

        # 5. Record to DB
        record = BattleRecord(
            account_id=account.id,
            timestamp=datetime.now(timezone.utc),
            opponent_id=target_id,
            opponent_name=target_name,
            opponent_power=target_defense,
            result=result_str,
            gold_earned=gold_earned,
            xp_earned=xp_earned,
            cards_used=json.dumps(battle_card_ids),
            duration_ms=duration_ms
        )
        await BattleRepository.add(db, record)

        # Update Account in DB and clear error
        acc_updates = {
            "gold": account.gold + gold_earned,
            "xp": account.xp + xp_earned,
            "last_error": None,
            "last_activity": datetime.now(timezone.utc),
            "last_successful_request": datetime.now(timezone.utc)
        }
        if "player" in res and isinstance(res["player"], dict):
            if "gold" in res["player"]:
                acc_updates["gold"] = int(res["player"]["gold"])
            if "xp" in res["player"]:
                acc_updates["xp"] = int(res["player"]["xp"])
        await AccountRepository.update(db, account.id, acc_updates)

        # Activity log
        await ActivityRepository.add(db, ActivityLog(
            account_id=account.id,
            account_name=account.name,
            event_type="BATTLE_WON" if result_str == "WIN" else "BATTLE_LOST",
            message=f"Battle {result_str} vs {target_name}: +{gold_earned:,} Gold, +{xp_earned:,} XP ({duration_ms}ms)",
            metadata_json=json.dumps({
                "opponent": target_name,
                "result": result_str,
                "gold": gold_earned,
                "xp": xp_earned
            })
        ))

        # Notify
        await notification_service.notify(
            db=db,
            title="Battle Finished",
            message=f"{account.name} {result_str} battle against {target_name} (+{gold_earned:,} Gold)",
            priority="INFO",
            event_type="BATTLE_FINISHED",
            account_id=account.id,
            account_name=account.name,
            metadata={
                "opponent_name": target_name,
                "result": result_str,
                "gold_earned": gold_earned,
                "xp_earned": xp_earned
            }
        )
        await db.commit()

        return {
            "result": result_str,
            "opponent": target_name,
            "opponent_power": target_defense,
            "gold_earned": gold_earned,
            "xp_earned": xp_earned,
            "cards_used": battle_card_ids,
            "duration_ms": duration_ms
        }


battle_service = BattleService()
