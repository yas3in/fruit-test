"""Battle API endpoints (Section 41 & 52)."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.database import get_db
from src.fruitcraft_bot.core.security import get_current_admin
from src.fruitcraft_bot.services.battle_service import battle_service
from src.fruitcraft_bot.automation.worker_manager import worker_manager

router = APIRouter(tags=["Battles"])


class BattleStartRequest(BaseModel):
    strategy: Optional[str] = "highest_power"
    max_battles: Optional[int] = 50
    min_gold: Optional[int] = 1000
    max_opponent_defense: Optional[int] = 100000
    delay_min: Optional[float] = 3.0
    delay_max: Optional[float] = 6.0


@router.get("/api/accounts/{account_id}/battles")
async def get_account_battles(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return await battle_service.get_battle_summary(account_id, db)


@router.post("/api/accounts/{account_id}/workers/battle/start")
async def start_battle_worker(
    account_id: str,
    req: Optional[BattleStartRequest] = None,
    admin: str = Depends(get_current_admin)
):
    conf = req.model_dump() if req else {}
    return await worker_manager.start_worker(account_id, "BattleWorker", conf)


@router.post("/api/accounts/{account_id}/workers/battle/stop")
async def stop_battle_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.stop_worker(account_id, "BattleWorker")


@router.post("/api/accounts/{account_id}/workers/battle/pause")
async def pause_battle_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.pause_worker(account_id, "BattleWorker")


@router.post("/api/accounts/{account_id}/workers/battle/resume")
async def resume_battle_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.resume_worker(account_id, "BattleWorker")
