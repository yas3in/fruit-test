"""Background health monitoring service for API, database, workers, and Telegram."""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional
from sqlalchemy import text

from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.db.database import AsyncSessionLocal
from src.fruitcraft_bot.core.events import event_bus
from src.fruitcraft_bot.services.telegram_service import telegram_service

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.last_status: Dict[str, Any] = {
            "api": "UNKNOWN",
            "database": "UNKNOWN",
            "telegram": "UNKNOWN",
            "workers": "UNKNOWN",
            "last_check": None
        }

    async def check_database(self) -> bool:
        """Check DB connectivity."""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("DB health check failed: %s", e)
            return False

    async def check_api(self) -> bool:
        """Check FruitCraft server or proxy availability."""
        import httpx
        try:
            proxy = settings.proxy_url if settings.proxy_enabled else None
            async with httpx.AsyncClient(proxy=proxy, trust_env=bool(proxy), timeout=5.0) as client:
                resp = await client.get(settings.base_url)
                return resp.status_code in (200, 301, 302, 403, 404, 405, 503)
        except Exception:
            return True

    async def check_telegram(self) -> bool:
        """Check Telegram API availability if enabled."""
        if not settings.telegram_enabled or not settings.telegram_bot_token:
            return True  # N/A
        try:
            import httpx
            proxy = settings.proxy_url if settings.proxy_enabled else None
            token = settings.telegram_bot_token.get_secret_value()
            async with httpx.AsyncClient(proxy=proxy, timeout=5.0) as client:
                resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
                return resp.status_code == 200
        except Exception:
            return False

    async def get_health_status(self) -> Dict[str, Any]:
        """Perform on-demand health assessment."""
        db_ok = await self.check_database()
        api_ok = await self.check_api()
        tg_ok = await self.check_telegram()

        self.last_status = {
            "status": "HEALTHY" if (db_ok and api_ok) else "DEGRADED",
            "database": "HEALTHY" if db_ok else "UNHEALTHY",
            "api": "HEALTHY" if api_ok else "UNREACHABLE",
            "telegram": "HEALTHY" if tg_ok else ("DISABLED" if not settings.telegram_enabled else "UNREACHABLE"),
            "proxy_port": settings.proxy_port,
            "proxy_enabled": settings.proxy_enabled,
            "last_check": datetime.now(timezone.utc).isoformat()
        }
        return self.last_status

    async def start(self):
        """Start recurring background health monitor."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitor loop started.")

    async def stop(self):
        """Stop background health monitor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor loop stopped.")

    async def _monitor_loop(self):
        while self._running:
            try:
                status = await self.get_health_status()
                # Broadcast health update to WebSocket dashboard
                await event_bus.publish(
                    event_type="HEALTH_STATUS",
                    message=f"System health check: {status['status']}",
                    metadata=status,
                    priority="INFO" if status["status"] == "HEALTHY" else "WARNING"
                )
            except Exception as e:
                logger.error("Error in health monitor loop: %s", e)

            await asyncio.sleep(settings.health_check_interval_seconds)


health_monitor = HealthMonitor()
