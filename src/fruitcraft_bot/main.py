"""Main FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.db.database import init_db, AsyncSessionLocal
from src.fruitcraft_bot.db.models import Account
from src.fruitcraft_bot.db.repository import AccountRepository
from src.fruitcraft_bot.services.health_monitor import health_monitor
from src.fruitcraft_bot.services.player_service import player_service

# Import API routers
from src.fruitcraft_bot.api.auth import router as auth_router
from src.fruitcraft_bot.api.accounts import router as accounts_router
from src.fruitcraft_bot.api.battles import router as battles_router
from src.fruitcraft_bot.api.mine import router as mine_router
from src.fruitcraft_bot.api.quests import router as quests_router
from src.fruitcraft_bot.api.cards import router as cards_router
from src.fruitcraft_bot.api.workers import router as workers_router
from src.fruitcraft_bot.api.events import router as events_router
from src.fruitcraft_bot.api.settings import router as settings_router
from src.fruitcraft_bot.api.health import router as health_router
from src.fruitcraft_bot.api.websocket import router as ws_router

logging.basicConfig(
    level=getattr(logging, settings.logging_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fruitcraft_bot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing FruitCraft Automation System...")
    await init_db()

    # Pre-seed initial account from .env if table is empty and restore_key exists
    env_restore_key = os.getenv("FRUITCRAFT_RESTORE_KEY")
    if env_restore_key:
        async with AsyncSessionLocal() as session:
            accounts = await AccountRepository.get_all(session)
            if not accounts:
                logger.info("Seeding initial account from .env: FRUITCRAFT_RESTORE_KEY")
                initial_acc = Account(
                    id="main",
                    name="Main Account",
                    restore_key=env_restore_key.strip(),
                    is_active=True,
                    current_state="READY"
                )
                await AccountRepository.create(session, initial_acc)
                await session.commit()

    # Enforce clean environment variables when direct connection is configured
    if not settings.proxy_enabled:
        for var in ("http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
            os.environ.pop(var, None)

    # Initial sync for registered accounts
    async def initial_sync():
        async with AsyncSessionLocal() as session:
            accs = await AccountRepository.get_all(session)
            for acc in accs:
                try:
                    await player_service.sync_player(acc.id, session)
                except Exception as e:
                    logger.warning("Initial sync for account %s: %s", acc.name, e)

    asyncio.create_task(initial_sync())

    # Start health monitor
    await health_monitor.start()

    logger.info("System startup complete. Ready for dashboard requests.")
    yield

    # Shutdown
    logger.info("Shutting down system...")
    await health_monitor.stop()


app = FastAPI(
    title="FruitCraft Automation Dashboard API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(battles_router)
app.include_router(mine_router)
app.include_router(quests_router)
app.include_router(cards_router)
app.include_router(workers_router)
app.include_router(events_router)
app.include_router(settings_router)
app.include_router(health_router)
app.include_router(ws_router)

# Mount frontend if build exists
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
