"""Account management API routes (Section 45 & 53)."""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.database import get_db
from src.fruitcraft_bot.db.models import Account, ActivityLog
from src.fruitcraft_bot.db.repository import AccountRepository, ActivityRepository
from src.fruitcraft_bot.core.security import get_current_admin, mask_secret
from src.fruitcraft_bot.services.player_service import player_service
from src.fruitcraft_bot.automation.worker_manager import worker_manager

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


class AccountCreateRequest(BaseModel):
    name: str
    restore_key: str
    is_active: bool = True


class AccountUpdateRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: str
    name: str
    masked_restore_key: str
    is_active: bool
    player_id: Optional[int]
    player_name: Optional[str]
    level: int
    xp: int
    gold: int
    nectar: int
    potion: int
    global_rank: Optional[int]
    league_rank: Optional[int]
    tribe_name: Optional[str]
    attack_power: int
    defense_power: int
    current_state: str
    battle_worker_status: str
    mine_worker_status: str
    quest_worker_status: str
    last_activity: Optional[str]
    next_action: Optional[str]
    last_error: Optional[str]
    captcha_status: str
    last_successful_request: Optional[str]
    last_login: Optional[str]


def to_account_response(acc: Account) -> AccountResponse:
    return AccountResponse(
        id=acc.id,
        name=acc.name,
        masked_restore_key=mask_secret(acc.restore_key),
        is_active=acc.is_active,
        player_id=acc.player_id,
        player_name=acc.player_name,
        level=acc.level or 1,
        xp=acc.xp or 0,
        gold=acc.gold or 0,
        nectar=acc.nectar or 0,
        potion=acc.potion or 0,
        global_rank=acc.global_rank,
        league_rank=acc.league_rank,
        tribe_name=acc.tribe_name,
        attack_power=acc.attack_power or 0,
        defense_power=acc.defense_power or 0,
        current_state=acc.current_state or "STOPPED",
        battle_worker_status=acc.battle_worker_status or "STOPPED",
        mine_worker_status=acc.mine_worker_status or "STOPPED",
        quest_worker_status=acc.quest_worker_status or "STOPPED",
        last_activity=acc.last_activity.isoformat() if acc.last_activity else None,
        next_action=acc.next_action,
        last_error=acc.last_error,
        captcha_status=acc.captcha_status or "NONE",
        last_successful_request=acc.last_successful_request.isoformat() if acc.last_successful_request else None,
        last_login=acc.last_login.isoformat() if acc.last_login else None
    )


@router.get("", response_model=List[AccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    accounts = await AccountRepository.get_all(db)
    return [to_account_response(a) for a in accounts]


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    req: AccountCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    acc_id = str(uuid.uuid4())[:8]
    account = Account(
        id=acc_id,
        name=req.name,
        restore_key=req.restore_key.strip(),
        is_active=req.is_active,
        current_state="READY"
    )
    saved = await AccountRepository.create(db, account)

    # Activity log
    await ActivityRepository.add(db, ActivityLog(
        account_id=acc_id,
        account_name=req.name,
        event_type="ACCOUNT_ADDED",
        message=f"Added account '{req.name}'"
    ))

    # Trigger background initial sync
    try:
        await player_service.sync_player(acc_id, db)
        updated = await AccountRepository.get_by_id(db, acc_id)
        if updated:
            saved = updated
    except Exception:
        pass

    return to_account_response(saved)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    acc = await AccountRepository.get_by_id(db, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return to_account_response(acc)


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    req: AccountUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    acc = await AccountRepository.get_by_id(db, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    updates = {}
    if req.name is not None:
        updates["name"] = req.name
    if req.is_active is not None:
        updates["is_active"] = req.is_active
        if not req.is_active:
            # Stop all workers when disabled
            await worker_manager.stop_all_for_account(account_id)
            updates["current_state"] = "STOPPED"

    updated = await AccountRepository.update(db, account_id, updates)
    return to_account_response(updated)


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    acc = await AccountRepository.get_by_id(db, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    await worker_manager.stop_all_for_account(account_id)
    await AccountRepository.delete(db, account_id)
    return {"message": "Account removed successfully"}


@router.post("/{account_id}/sync", response_model=AccountResponse)
async def sync_account_player(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    acc = await AccountRepository.get_by_id(db, account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    await player_service.sync_player(account_id, db)
    updated = await AccountRepository.get_by_id(db, account_id)
    return to_account_response(updated)
