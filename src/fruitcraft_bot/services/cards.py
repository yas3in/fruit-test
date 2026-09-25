"""Card management service, selection strategies, evolution, potionization, and healing."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from fruitcraft_bot.api.models import BaseModel, Field

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.models import (
    CardModel,
    CollectGoldRequest,
    CollectGoldResult,
    CoolOffRequest,
    EvolveRequest,
    PotionizeRequest,
)
from fruitcraft_bot.services.auth import AuthService

logger = logging.getLogger("fruitcraft.services.cards")


class CardsSelection(BaseModel):
    """Selected deck parameters for battle or quest."""
    cards: List[int]
    hero_id: Optional[int] = None
    no_heal: bool = False


# ============================================================================
# Card Selection Strategies
# ============================================================================

class CardSelectionStrategy(ABC):
    """Abstract base for card deck selection."""

    @abstractmethod
    def select(self, available_cards: List[CardModel], count: int = 4) -> CardsSelection:
        pass


class StrongestCardsStrategy(CardSelectionStrategy):
    """Select N usable cards with highest attack/power rating."""

    def select(self, available_cards: List[CardModel], count: int = 4) -> CardsSelection:
        if not available_cards:
            return CardsSelection(cards=[])

        import time
        now = int(time.time())
        usable_cards = [c for c in available_cards if c.is_usable(now)]

        if not usable_cards:
            logger.warning("No usable (non-cooldown) cards found in deck.")
            return CardsSelection(cards=[])

        sorted_cards = sorted(usable_cards, key=lambda c: c.power, reverse=True)
        selected = sorted_cards[:count]
        return CardsSelection(cards=[c.id for c in selected])


class WeakestCardsStrategy(CardSelectionStrategy):
    """Select N usable cards with lowest attack/power rating."""

    def select(self, available_cards: List[CardModel], count: int = 4) -> CardsSelection:
        if not available_cards:
            return CardsSelection(cards=[])

        import time
        now = int(time.time())
        usable_cards = [c for c in available_cards if c.is_usable(now)]

        if not usable_cards:
            logger.warning("No usable (non-cooldown) cards found in deck.")
            return CardsSelection(cards=[])

        sorted_cards = sorted(usable_cards, key=lambda c: c.power)
        selected = sorted_cards[:count]
        return CardsSelection(cards=[c.id for c in selected])


class SpecificCardsStrategy(CardSelectionStrategy):
    """Select specific card IDs provided in list."""

    def __init__(self, card_ids: List[int]):
        self.card_ids = card_ids

    def select(self, available_cards: List[CardModel], count: int = 4) -> CardsSelection:
        return CardsSelection(cards=self.card_ids[:count])


class CustomSelectionStrategy(CardSelectionStrategy):
    """Custom selection filter based on health or hero association."""

    def select(self, available_cards: List[CardModel], count: int = 4) -> CardsSelection:
        usable = [c for c in available_cards if not c.in_cooldown]
        if not usable:
            usable = available_cards
        sorted_cards = sorted(usable, key=lambda c: c.power, reverse=True)
        return CardsSelection(cards=[c.id for c in sorted_cards[:count]])


# ============================================================================
# Card Service
# ============================================================================

class CardService:
    """Manages cards, evolution, potions, cooldowns, and gold collection."""

    def __init__(self, api_client: FruitCraftAPIClient, auth_service: AuthService):
        self.client = api_client
        self.auth = auth_service

    async def collect_gold(self) -> CollectGoldResult:
        """Call POST cards/collectgold."""
        logger.info("Executing cards/collectgold...")
        req = CollectGoldRequest(client="android")
        resp = await self.client.request("cards/collectgold", req)

        data = resp.data if isinstance(resp.data, dict) else {}

        result = CollectGoldResult(
            collected_gold=int(data.get("collected_gold", data.get("gold", 0))),
            player_gold=int(data.get("player_gold", 0)),
            gold_collection_allowed=bool(data.get("gold_collection_allowed", False)),
            gold_collection_allowed_at=data.get("gold_collection_allowed_at"),
            gold_collection_extraction=int(data.get("gold_collection_extraction", 0)),
            last_gold_collected_at=data.get("last_gold_collected_at"),
            needs_captcha=resp.needs_captcha,
        )

        if self.auth.player_info and result.player_gold > 0:
            self.auth.player_info.gold = result.player_gold

        logger.info("Gold collection result: collected=%d, player_total=%d, allowed_next=%s", result.collected_gold, result.player_gold, result.gold_collection_allowed_at)
        return result

    async def potionize(self, hero_id: int, amount: int = 1) -> Dict[str, Any]:
        """Call POST cards/potionize."""
        req = PotionizeRequest(hero_id=hero_id, amount=amount)
        logger.info("Applying %d potions to hero %d...", amount, hero_id)
        resp = await self.client.request("cards/potionize", req)
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}

    async def cool_off(self, card_id: int) -> Dict[str, Any]:
        """Call POST cards/cooloff for single card."""
        req = CoolOffRequest(card_id=card_id)
        logger.info("Cooling off card %d...", card_id)
        resp = await self.client.request("cards/cooloff", req)
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}

    async def heal_all(self, card_ids: List[int], max_gold_spend: int = 50000) -> List[Dict[str, Any]]:
        """Cool off / heal multiple damaged cards within spending limits."""
        logger.info("Healing %d cards up to max gold %d...", len(card_ids), max_gold_spend)
        results = []
        spent_gold = 0

        for cid in card_ids:
            if spent_gold >= max_gold_spend:
                logger.warning("Reached max gold spend limit (%d) for healing.", max_gold_spend)
                break
            res = await self.cool_off(cid)
            results.append(res)
            cost = int(res.get("gold_cost", res.get("cost", 0)))
            spent_gold += cost

        return results

    async def evolve_card(self, sacrifices: List[int], auto_select: bool = False) -> Dict[str, Any]:
        """
        Call POST cards/evolve with sacrifice card IDs.
        Automatic selection is disabled by default to prevent accidental consumption of valuable cards.
        """
        if not sacrifices and not auto_select:
            raise ValueError("Sacrifice card list must be specified unless auto_select is explicitly enabled.")

        if auto_select and not sacrifices:
            # Safe placeholder guard: require manual sacrifice IDs by default
            raise ValueError("Automatic card selection for evolution must be explicitly configured with sacrifice card IDs.")

        req = EvolveRequest(sacrifices=sacrifices)
        logger.info("Evolving card by sacrificing %d cards...", len(sacrifices))
        resp = await self.client.request("cards/evolve", req)
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}

    async def fruits_json_export(self) -> Dict[str, Any]:
        """Call POST cards/fruitsjsonexport."""
        logger.info("Exporting fruits cards JSON...")
        resp = await self.client.request("cards/fruitsjsonexport", {})
        return resp.data if isinstance(resp.data, dict) else {"raw": resp.data}
