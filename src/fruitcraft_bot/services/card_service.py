"""Card collection management with safety confirmation checks."""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.fruitcraft_bot.db.repository import AccountRepository, ActivityRepository
from src.fruitcraft_bot.db.models import ActivityLog
from src.fruitcraft_bot.fruitbot_wrapper.pool import client_pool
from src.fruitcraft_bot.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class CardService:
    @staticmethod
    async def get_cards(account_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """Retrieve all player cards formatted for cards table/grid."""
        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            return []

        client = await client_pool.get_client(account.id, account.restore_key)
        try:
            col = await client.get_my_collection()
            cards_raw = col.get("cards", col)
            if isinstance(cards_raw, dict):
                cards_list = list(cards_raw.values())
            elif isinstance(cards_raw, list):
                cards_list = cards_raw
            else:
                cards_list = []

            formatted = []
            for c in cards_list:
                if not isinstance(c, dict):
                    continue
                cid = c.get("id", c.get("card_id"))
                formatted.append({
                    "id": cid,
                    "name": c.get("name", f"Card #{cid}"),
                    "level": c.get("level", 1),
                    "attack": c.get("power", c.get("attack", 0)),
                    "defense": c.get("defense", 0),
                    "rarity": c.get("rarity", c.get("category", 1)),
                    "potion": c.get("potion", 0),
                    "cooldown": c.get("in_cooldown", False),
                    "status": "In Cooldown" if c.get("in_cooldown") else "Ready"
                })
            return formatted
        except Exception as e:
            logger.error("Failed to fetch cards for account %s: %s", account_id, e)
            return []

    @staticmethod
    async def evolve_card(
        account_id: str,
        sacrifice_card_ids: List[int],
        confirmed: bool,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Evolve card using sacrifices.
        CRITICAL SAFETY: Requires explicit confirmed=True confirmation!
        """
        if not confirmed:
            raise ValueError("Confirmation required to evolve cards. Operation cancelled.")

        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found.")

        client = await client_pool.get_client(account.id, account.restore_key)
        res = await client.evolve_card(sacrifice_card_ids)

        await ActivityRepository.add(db, ActivityLog(
            account_id=account.id,
            account_name=account.name,
            event_type="CARD_EVOLVED",
            message=f"Evolved card with sacrifices: {sacrifice_card_ids}"
        ))

        await notification_service.notify(
            db=db,
            title="Card Evolved",
            message=f"Account {account.name} successfully evolved card.",
            priority="INFO",
            event_type="CARD_EVOLVED",
            account_id=account.id,
            account_name=account.name
        )
        return res

    @staticmethod
    async def cooloff_card(
        account_id: str,
        card_id: int,
        confirmed: bool,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Cool off a card spending gold. Requires confirmed=True."""
        if not confirmed:
            raise ValueError("Confirmation required to purchase cooldown. Operation cancelled.")

        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found.")

        client = await client_pool.get_client(account.id, account.restore_key)
        res = await client.cooloff_card(card_id)

        await ActivityRepository.add(db, ActivityLog(
            account_id=account.id,
            account_name=account.name,
            event_type="COOLDOWN_PURCHASED",
            message=f"Purchased cooldown for card #{card_id}"
        ))
        return res

    @staticmethod
    async def potionize_hero(
        account_id: str,
        hero_id: int,
        amount: int,
        confirmed: bool,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply potion to hero. Requires confirmed=True."""
        if not confirmed:
            raise ValueError("Confirmation required to use potions. Operation cancelled.")

        account = await AccountRepository.get_by_id(db, account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found.")

        client = await client_pool.get_client(account.id, account.restore_key)
        res = await client.potionize_hero(amount=amount, hero_id=hero_id)

        await ActivityRepository.add(db, ActivityLog(
            account_id=account.id,
            account_name=account.name,
            event_type="POTION_USED",
            message=f"Used {amount} potion(s) on hero #{hero_id}"
        ))
        return res


card_service = CardService()
