"""System Settings API endpoints (Section 58)."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.database import get_db
from src.fruitcraft_bot.core.security import get_current_admin
from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.db.repository import SettingsRepository

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class SystemSettingsDTO(BaseModel):
    # Battle defaults
    battle_delay_min: float
    battle_delay_max: float
    max_battles_per_run: int
    min_gold_threshold: int
    max_opponent_defense: int
    auto_heal: bool
    auto_cooldown: bool

    # Mine & Quest defaults
    mine_delay_minutes: int
    quest_delay_min: float
    quest_delay_max: float
    max_quests_per_run: int

    # Worker & Health policy
    auto_restart_workers: bool
    stop_on_captcha: bool
    stop_on_error: bool

    # Telegram settings (Masked/boolean)
    telegram_enabled: bool
    telegram_chat_id: Optional[str]
    has_telegram_token: bool

    # Proxy settings (Default port 10501)
    proxy_enabled: bool
    proxy_port: int
    proxy_url: str

    # System & Timezone
    timezone: str
    daily_report_time: str
    logging_level: str


@router.get("", response_model=SystemSettingsDTO)
async def get_system_settings(
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    overrides = await SettingsRepository.get(db, "global_settings", {})

    return SystemSettingsDTO(
        battle_delay_min=overrides.get("battle_delay_min", settings.battle_delay_min),
        battle_delay_max=overrides.get("battle_delay_max", settings.battle_delay_max),
        max_battles_per_run=overrides.get("max_battles_per_run", settings.max_battles_per_run),
        min_gold_threshold=overrides.get("min_gold_threshold", settings.min_gold_threshold),
        max_opponent_defense=overrides.get("max_opponent_defense", settings.max_opponent_defense),
        auto_heal=overrides.get("auto_heal", settings.auto_heal),
        auto_cooldown=overrides.get("auto_cooldown", settings.auto_cooldown),
        mine_delay_minutes=overrides.get("mine_delay_minutes", settings.mine_delay_minutes),
        quest_delay_min=overrides.get("quest_delay_min", settings.quest_delay_min),
        quest_delay_max=overrides.get("quest_delay_max", settings.quest_delay_max),
        max_quests_per_run=overrides.get("max_quests_per_run", settings.max_quests_per_run),
        auto_restart_workers=overrides.get("auto_restart_workers", settings.auto_restart_workers),
        stop_on_captcha=overrides.get("stop_on_captcha", settings.stop_on_captcha),
        stop_on_error=overrides.get("stop_on_error", settings.stop_on_error),
        telegram_enabled=overrides.get("telegram_enabled", settings.telegram_enabled),
        telegram_chat_id=overrides.get("telegram_chat_id", settings.telegram_chat_id),
        has_telegram_token=bool(settings.telegram_bot_token),
        proxy_enabled=overrides.get("proxy_enabled", settings.proxy_enabled),
        proxy_port=overrides.get("proxy_port", settings.proxy_port),
        proxy_url=overrides.get("proxy_url", settings.proxy_url),
        timezone=overrides.get("timezone", settings.timezone),
        daily_report_time=overrides.get("daily_report_time", settings.daily_report_time),
        logging_level=overrides.get("logging_level", settings.logging_level)
    )


@router.post("")
async def update_system_settings(
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    # Store settings in DB
    existing = await SettingsRepository.get(db, "global_settings", {})
    existing.update(updates)
    await SettingsRepository.set(db, "global_settings", existing)
    return {"message": "Settings updated successfully", "settings": existing}
