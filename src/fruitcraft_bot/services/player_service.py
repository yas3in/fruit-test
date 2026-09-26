"""Player synchronization and profile service."""

from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.repository import AccountRepository, ActivityRepository
from src.fruitcraft_bot.db.models import ActivityLog
from src.fruitcraft_bot.fruitbot_wrapper.pool import client_pool
from src.fruitcraft_bot.services.notification_service import notification_service
import fruitbot.exceptions as fb_exceptions

logger = logging.getLogger(__name__)


class PlayerService:
    @staticmethod
    async def sync_player(account_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Fetch fresh player data from FruitCraft server and persist to database."""
        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            return None

        client = await client_pool.get_client(account.id, account.restore_key)
        try:
            player_data = await client.load_player(save_session=True)
            now = datetime.now(timezone.utc)

            tribe_info = player_data.get("tribe") or {}
            updates = {
                "player_id": player_data.get("id"),
                "player_name": player_data.get("name"),
                "avatar_id": player_data.get("avatar_id"),
                "level": player_data.get("level", 1),
                "xp": player_data.get("xp", 0),
                "gold": player_data.get("gold", 0),
                "nectar": player_data.get("nectar", 0),
                "potion": player_data.get("potion", 0),
                "tribe_id": tribe_info.get("id"),
                "tribe_name": tribe_info.get("name"),
                "attack_power": player_data.get("attack_power", player_data.get("attack", 0)),
                "defense_power": player_data.get("defense_power", player_data.get("defense", 0)),
                "last_successful_request": now,
                "last_activity": now,
                "last_login": now,
                "captcha_status": "NONE"
            }

            if account.current_state in ("ERROR", "CAPTCHA REQUIRED"):
                updates["current_state"] = "READY"

            await AccountRepository.update(db, account.id, updates)

            # Record sync activity
            activity = ActivityLog(
                account_id=account.id,
                account_name=account.name,
                timestamp=now,
                event_type="PLAYER_SYNC",
                message=f"Synced profile for {player_data.get('name')}: Level {player_data.get('level')}, {player_data.get('gold'):,} Gold",
                metadata_json="{}"
            )
            await ActivityRepository.add(db, activity)
            return player_data

        except fb_exceptions.CaptchaRequired:
            await AccountRepository.update(db, account.id, {
                "current_state": "CAPTCHA REQUIRED",
                "captcha_status": "REQUIRED",
                "last_error": "CAPTCHA verification required by server"
            })
            await notification_service.notify(
                db=db,
                title="CAPTCHA Required",
                message=f"CAPTCHA required on account {account.name}. Automation paused.",
                priority="CRITICAL",
                event_type="CAPTCHA_REQUIRED",
                account_id=account.id,
                account_name=account.name,
                deduplication_key=f"{account.id}_captcha"
            )
            raise
        except Exception as e:
            err_msg = str(e)
            await AccountRepository.update(db, account.id, {
                "last_error": err_msg
            })
            await notification_service.notify(
                db=db,
                title="Player Sync Error",
                message=f"Failed to sync player for {account.name}: {err_msg}",
                priority="ERROR",
                event_type="API_ERROR",
                account_id=account.id,
                account_name=account.name,
                deduplication_key=f"{account.id}_sync_error"
            )
            raise


player_service = PlayerService()
