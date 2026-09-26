"""Worker control API endpoints (Section 46 & 52)."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.fruitcraft_bot.core.security import get_current_admin
from src.fruitcraft_bot.automation.worker_manager import worker_manager

router = APIRouter(tags=["Workers"])


class WorkerControlRequest(BaseModel):
    action: str  # "start", "stop", "pause", "resume", "restart"
    config: Optional[Dict[str, Any]] = None


@router.get("/api/workers")
async def get_all_workers(
    admin: str = Depends(get_current_admin)
):
    """Retrieve all workers across all accounts."""
    return await worker_manager.get_all_workers()


@router.get("/api/accounts/{account_id}/workers")
async def get_account_workers(
    account_id: str,
    admin: str = Depends(get_current_admin)
):
    """Retrieve workers specifically for one account."""
    return await worker_manager.get_all_workers(account_id=account_id)


@router.post("/api/accounts/{account_id}/workers/{worker_type}/control")
async def control_worker(
    account_id: str,
    worker_type: str,
    req: WorkerControlRequest,
    admin: str = Depends(get_current_admin)
):
    act = req.action.lower()
    if act == "start":
        return await worker_manager.start_worker(account_id, worker_type, req.config)
    elif act == "stop":
        return await worker_manager.stop_worker(account_id, worker_type)
    elif act == "pause":
        return await worker_manager.pause_worker(account_id, worker_type)
    elif act == "resume":
        return await worker_manager.resume_worker(account_id, worker_type)
    elif act == "restart":
        return await worker_manager.restart_worker(account_id, worker_type)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")
