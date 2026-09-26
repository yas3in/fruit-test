"""Activity feed and Notifications API endpoints (Sections 40, 47, 52, 55)."""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.database import get_db
from src.fruitcraft_bot.core.security import get_current_admin
from src.fruitcraft_bot.db.repository import ActivityRepository, NotificationRepository

router = APIRouter(tags=["Events & Notifications"])


class ActivityResponse(BaseModel):
    id: int
    timestamp: str
    account_id: Optional[str]
    account_name: str
    event_type: str
    message: str
    metadata: dict


class NotificationResponse(BaseModel):
    id: int
    timestamp: str
    account_id: Optional[str]
    account_name: str
    priority: str
    title: str
    message: str
    occurrence_count: int
    last_occurrence: str
    is_read: bool


@router.get("/api/events", response_model=List[ActivityResponse])
async def list_events(
    account_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    activities = await ActivityRepository.get_recent(db, limit=limit, account_id=account_id)
    res = []
    for a in activities:
        meta = {}
        if a.metadata_json:
            try:
                meta = json.loads(a.metadata_json)
            except Exception:
                pass
        res.append(ActivityResponse(
            id=a.id,
            timestamp=a.timestamp.isoformat() if a.timestamp else "",
            account_id=a.account_id,
            account_name=a.account_name,
            event_type=a.event_type,
            message=a.message,
            metadata=meta
        ))
    return res


@router.get("/api/notifications", response_model=List[NotificationResponse])
async def list_notifications(
    priority: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin)
):
    notifs = await NotificationRepository.get_recent(db, limit=limit, priority=priority)
    return [
        NotificationResponse(
            id=n.id,
            timestamp=n.timestamp.isoformat() if n.timestamp else "",
            account_id=n.account_id,
            account_name=n.account_name,
            priority=n.priority,
            title=n.title,
            message=n.message,
            occurrence_count=n.occurrence_count,
            last_occurrence=n.last_occurrence.isoformat() if n.last_occurrence else "",
            is_read=n.is_read
        )
        for n in notifs
    ]
