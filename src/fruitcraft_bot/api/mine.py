"""Mine API endpoints (Section 42 & 52)."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.database import get_db
from src.fruitcraft_bot.core.security import get_current_admin
from src.fruitcraft_bot.services.mine_service import mine_service
from src.fruitcraft_bot.automation.worker_manager import worker_manager

router = APIRouter(tags=["Mine"])


class MineStartRequest(BaseModel):
    interval_minutes: Optional[int] = 30


@router.get("/api/accounts/{account_id}/mine")
async def get_mine_info(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return await mine_service.get_mine_info(account_id, db)


@router.post("/api/accounts/{account_id}/mine/collect")
async def collect_mined_gold_now(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return await mine_service.collect_gold(account_id, db)


@router.post("/api/accounts/{account_id}/workers/mine/start")
async def start_mine_worker(
    account_id: str,
    req: Optional[MineStartRequest] = None,
    admin: str = Depends(get_current_admin)
):
    conf = req.model_dump() if req else {}
    return await worker_manager.start_worker(account_id, "MineWorker", conf)


@router.post("/api/accounts/{account_id}/workers/mine/stop")
async def stop_mine_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.stop_worker(account_id, "MineWorker")


@router.post("/api/accounts/{account_id}/workers/mine/pause")
async def pause_mine_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.pause_worker(account_id, "MineWorker")


@router.post("/api/accounts/{account_id}/workers/mine/resume")
async def resume_mine_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.resume_worker(account_id, "MineWorker")
