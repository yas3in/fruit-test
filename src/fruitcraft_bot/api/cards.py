"""Card Management API endpoints with explicit confirmation (Section 44 & 52)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.database import get_db
from src.fruitcraft_bot.core.security import get_current_admin
from src.fruitcraft_bot.services.card_service import card_service

router = APIRouter(tags=["Cards"])


class EvolveRequest(BaseModel):
    sacrifice_card_ids: List[int]
    confirmed: bool = False


class CooloffRequest(BaseModel):
    card_id: int
    confirmed: bool = False


class PotionizeRequest(BaseModel):
    hero_id: int
    amount: int = 1
    confirmed: bool = False


@router.get("/api/accounts/{account_id}/cards")
async def get_cards(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    """Retrieve card collection. Read-only: never performs resource actions on page view."""
    return await card_service.get_cards(account_id, db)


@router.post("/api/accounts/{account_id}/cards/evolve")
async def evolve_card(
    account_id: str,
    req: EvolveRequest,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    if not req.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required before evolving cards."
        )
    try:
        return await card_service.evolve_card(
            account_id=account_id,
            sacrifice_card_ids=req.sacrifice_card_ids,
            confirmed=True,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/accounts/{account_id}/cards/cooloff")
async def cooloff_card(
    account_id: str,
    req: CooloffRequest,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    if not req.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required before spending gold on cooldown."
        )
    try:
        return await card_service.cooloff_card(
            account_id=account_id,
            card_id=req.card_id,
            confirmed=True,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/accounts/{account_id}/cards/potionize")
async def potionize_hero(
    account_id: str,
    req: PotionizeRequest,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    if not req.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required before applying potions."
        )
    try:
        return await card_service.potionize_hero(
            account_id=account_id,
            hero_id=req.hero_id,
            amount=req.amount,
            confirmed=True,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
