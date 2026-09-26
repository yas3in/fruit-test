"""Health check endpoint (Section 52 & 57)."""

from fastapi import APIRouter
from src.fruitcraft_bot.services.health_monitor import health_monitor

router = APIRouter(tags=["Health"])


@router.get("/api/health")
async def get_system_health():
    """System health check endpoint."""
    return await health_monitor.get_health_status()
