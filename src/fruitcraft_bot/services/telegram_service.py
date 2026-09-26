"""Telegram Bot notifications and interactive commands handler."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx

from src.fruitcraft_bot.core.config import settings

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Sends formatted alerts and summaries to Telegram with proxy support (port 10501)."""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token.get_secret_value() if settings.telegram_bot_token else None
        self.chat_id = settings.telegram_chat_id
        self.enabled = settings.telegram_enabled and bool(self.bot_token and self.chat_id)
        self.proxy_url = settings.proxy_url if settings.proxy_enabled else None

    def _get_http_client(self) -> httpx.AsyncClient:
        mounts = {}
        if self.proxy_url:
            return httpx.AsyncClient(proxy=self.proxy_url, timeout=15.0)
        return httpx.AsyncClient(timeout=15.0)

    async def send_message(self, text: str) -> bool:
        """Send plain or markdown message to configured Telegram chat."""
        if not self.enabled or not self.bot_token or not self.chat_id:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with self._get_http_client() as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return True
                logger.warning("Telegram send_message failed: %s %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Error sending Telegram message: %s", e)
            return False

    async def send_captcha_alert(self, account_name: str) -> bool:
        """Send urgent CAPTCHA alert (Section 48)."""
        time_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        msg = (
            "🚨 <b>FruitCraft Alert</b>\n\n"
            f"<b>Account:</b> {account_name}\n"
            "<b>Event:</b> <code>CAPTCHA_REQUIRED</code>\n\n"
            "Automation has been stopped.\n\n"
            f"<b>Time:</b> {time_str}"
        )
        return await self.send_message(msg)

    async def send_battle_result(
        self,
        account_name: str,
        opponent_name: str,
        result: str,
        gold_earned: int,
        xp_earned: int
    ) -> bool:
        """Send battle outcome alert."""
        icon = "🏆" if result == "WIN" else "💀"
        msg = (
            f"{icon} <b>FruitCraft Battle Result</b>\n\n"
            f"<b>Account:</b> {account_name}\n"
            f"<b>Opponent:</b> {opponent_name}\n"
            f"<b>Outcome:</b> <b>{result}</b>\n"
            f"<b>Gold:</b> +{gold_earned:,}\n"
            f"<b>XP:</b> +{xp_earned:,}"
        )
        return await self.send_message(msg)

    async def send_error(
        self,
        account_name: str,
        endpoint: str,
        error_message: str,
        repeated_failures: int = 1
    ) -> bool:
        """Send deduplicated error notification (Section 56)."""
        time_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        msg = (
            "⚠️ <b>FruitCraft API Error</b>\n\n"
            f"<b>Account:</b> {account_name}\n"
            f"<b>Endpoint:</b> <code>{endpoint}</code>\n"
            f"<b>Repeated failures:</b> {repeated_failures}\n"
            f"<b>Error:</b> {error_message}\n"
            f"<b>Last occurrence:</b> {time_str}"
        )
        return await self.send_message(msg)

    async def send_worker_status(
        self,
        account_name: str,
        worker_name: str,
        status: str,
        details: Optional[str] = None
    ) -> bool:
        """Send worker lifecycle status notification."""
        status_icons = {
            "RUNNING": "🟢",
            "STOPPED": "⚪",
            "PAUSED": "⏸",
            "ERROR": "🔴",
            "WAITING": "🟡"
        }
        icon = status_icons.get(status.upper(), "ℹ️")
        msg = (
            f"{icon} <b>Worker Status Update</b>\n\n"
            f"<b>Account:</b> {account_name}\n"
            f"<b>Worker:</b> {worker_name}\n"
            f"<b>Status:</b> {status}\n"
        )
        if details:
            msg += f"<b>Details:</b> {details}\n"
        return await self.send_message(msg)

    async def send_daily_summary(self, summary: Dict[str, Any]) -> bool:
        """Send daily summary report (Section 50)."""
        msg = (
            "📊 <b>FruitCraft Daily Report</b>\n\n"
            f"<b>Account:</b> {summary.get('account_name', 'All')}\n\n"
            f"<b>Battles:</b> {summary.get('battles_count', 0)}\n"
            f"<b>Wins:</b> {summary.get('wins', 0)}\n"
            f"<b>Losses:</b> {summary.get('losses', 0)}\n"
            f"<b>Gold earned:</b> +{summary.get('gold_earned', 0):,}\n"
            f"<b>Quests:</b> {summary.get('quests_count', 0)}\n"
            f"<b>Gold collections:</b> {summary.get('mine_collections', 0)}\n"
            f"<b>Cards upgraded:</b> {summary.get('cards_upgraded', 0)}\n"
            f"<b>Errors:</b> {summary.get('errors_count', 0)}\n"
            f"<b>Runtime:</b> {summary.get('runtime_str', 'N/A')}\n"
        )
        return await self.send_message(msg)


telegram_service = TelegramNotificationService()
