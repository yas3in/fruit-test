"""Quest API endpoints (Section 43 & 52)."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.database import get_db
from src.fruitcraft_bot.core.security import get_current_admin
from src.fruitcraft_bot.services.quest_service import quest_service
from src.fruitcraft_bot.automation.worker_manager import worker_manager

router = APIRouter(tags=["Quests"])


class QuestStartRequest(BaseModel):
    max_quests: Optional[int] = 30
    delay_min: Optional[float] = 4.0
    delay_max: Optional[float] = 8.0


@router.get("/api/accounts/{account_id}/quests")
async def get_quest_info(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return await quest_service.get_quest_info(account_id, db)


@router.post("/api/accounts/{account_id}/quests/execute")
async def execute_quest_now(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    return await quest_service.execute_quest_step(account_id, db)


@router.post("/api/accounts/{account_id}/workers/quest/start")
async def start_quest_worker(
    account_id: str,
    req: Optional[QuestStartRequest] = None,
    admin: str = Depends(get_current_admin)
):
    conf = req.model_dump() if req else {}
    return await worker_manager.start_worker(account_id, "QuestWorker", conf)


@router.post("/api/accounts/{account_id}/workers/quest/stop")
async def stop_quest_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.stop_worker(account_id, "QuestWorker")


@router.post("/api/accounts/{account_id}/workers/quest/pause")
async def pause_quest_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.pause_worker(account_id, "QuestWorker")


@router.post("/api/accounts/{account_id}/workers/quest/resume")
async def resume_quest_worker(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    return await worker_manager.resume_worker(account_id, "QuestWorker")
