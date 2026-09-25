"""Pydantic data models for FruitCraft requests and API responses."""

import json
from typing import Any, Dict, List, Optional, Union

try:
    from pydantic import BaseModel, Field
except ImportError:
    def Field(default: Any = None, default_factory: Any = None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        def __init__(self, **kwargs):
            # Populate class-level defaults first
            for cls in reversed(self.__class__.__mro__):
                for k, v in getattr(cls, "__annotations__", {}).items():
                    if hasattr(cls, k):
                        val = getattr(cls, k)
                        if callable(val) and not isinstance(val, type):
                            try:
                                setattr(self, k, val())
                            except Exception:
                                setattr(self, k, val)
                        else:
                            setattr(self, k, val)
                    else:
                        setattr(self, k, None)

            # Override with explicit kwargs
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
            res = {}
            for k, v in self.__dict__.items():
                if hasattr(v, "get_secret_value"):
                    res[k] = v.get_secret_value()
                elif isinstance(v, BaseModel):
                    res[k] = v.model_dump()
                elif isinstance(v, list):
                    res[k] = [item.model_dump() if isinstance(item, BaseModel) else item for item in v]
                else:
                    res[k] = v
            return res

        def model_dump_json(self, *args, **kwargs) -> str:
            return json.dumps(self.model_dump(), separators=(',', ':'))


# ============================================================================
# API Response Wrapping
# ============================================================================

class APIResponse(BaseModel):
    """Standard outer wrapper returned by FruitCraft endpoints."""
    status: bool = True
    data: Optional[Union[Dict[str, Any], List[Any], str, int]] = None
    needs_captcha: bool = False
    time: Optional[int] = None
    code: Optional[int] = 0
    message: Optional[str] = None


# ============================================================================
# Request Models
# ============================================================================

class PlayerLoadRequest(BaseModel):
    """Request schema for POST player/load."""
    game_version: str = "1.9.10691"
    udid: str = "0000000000000000"
    os_type: int = 2
    restore_key: str = ""
    os_version: str = "7.1.2"
    model: str = "google pixel 2"
    metrix_uid: str = "-"
    appsflyer_uid: str = "-"
    device_name: str = "unknown"
    store_type: str = "myket"


class CollectGoldRequest(BaseModel):
    """Request schema for POST cards/collectgold."""
    client: str = "android"


class BattleRequest(BaseModel):
    """Request schema for POST battle/battle."""
    id: str = ""
    opponent_id: str = ""
    cards: List[int] = Field(default_factory=list)
    hero_id: Optional[int] = None
    hero: Optional[int] = None
    check: Optional[str] = None


class QuestRequest(BaseModel):
    """Request schema for POST battle/quest."""
    cards: List[int] = Field(default_factory=list)
    hash: Optional[str] = None
    check: Optional[str] = None


class FillPotionRequest(BaseModel):
    """Request schema for POST player/fillpotion."""
    amount: int = 1


class PotionizeRequest(BaseModel):
    """Request schema for POST cards/potionize."""
    hero_id: int = 0
    amount: int = 1


class CoolOffRequest(BaseModel):
    """Request schema for POST cards/cooloff."""
    card_id: int = 0


class EvolveRequest(BaseModel):
    """Request schema for POST cards/evolve."""
    sacrifices: List[int] = Field(default_factory=list)


class LiveBattleHelpRequest(BaseModel):
    """Request schema for POST live-battle/help."""
    battle_id: str = ""


class SetCardForLiveBattleRequest(BaseModel):
    """Request schema for POST live-battle/setcardforlivebattle."""
    round: int = 1
    card: int = 0
    battle_id: str = ""


class LiveBattleRequest(BaseModel):
    """Request schema for POST live-battle/livebattle."""
    opponent_id: str = ""


class BuyCardPackRequest(BaseModel):
    """Experimental request schema for POST store/buycardpack."""
    pack_id: int = 1
    currency: str = "gold"


# ============================================================================
# Response Sub-Models
# ============================================================================

class CardModel(BaseModel):
    """Game Card representation."""
    id: int = 0
    name: str = "Card"
    power: int = 0
    health: int = 0
    level: int = 1
    hero_id: Optional[int] = None
    in_cooldown: bool = False
    cooldown_ends_at: Optional[int] = None

    def is_usable(self, now: Optional[int] = None) -> bool:
        """Check if card is available for battle/quest (not damaged or in cooldown)."""
        import time
        if now is None:
            now = int(time.time())
        if self.in_cooldown:
            return False
        if self.cooldown_ends_at and self.cooldown_ends_at > now:
            return False
        return True


class PlayerInfo(BaseModel):
    """Extracted player profile state."""
    id: str = ""
    name: str = ""
    level: int = 1
    xp: int = 0
    gold: int = 0
    nectar: int = 0
    potion: int = 0
    rank: int = 0
    league: int = 0
    league_rank: int = 0
    tribe: Optional[str] = None
    total_battles: int = 0
    won_battles: int = 0
    lost_battles: int = 0
    cards: List[CardModel] = Field(default_factory=list)
    hero_info: Dict[str, Any] = Field(default_factory=dict)
    mine_info: Dict[str, Any] = Field(default_factory=dict)
    gold_collection_allowed: bool = True
    gold_collection_allowed_at: Optional[int] = None


class Opponent(BaseModel):
    """Opponent candidate for battle."""
    id: str = ""
    name: str = ""
    rank: int = 0
    xp: int = 0
    gold: int = 0
    level: int = 1
    def_power: int = 0
    league_id: int = 0
    league_rank: int = 0
    avatar_id: int = 0
    power_ratio: float = 1.0
    tribe_name: Optional[str] = None


class BattleResult(BaseModel):
    """Outcome of a battle request."""
    won: bool = False
    gold_earned: int = 0
    xp_earned: int = 0
    opp_name: str = ""
    q: Optional[str] = None
    cards_damaged: List[int] = Field(default_factory=list)
    needs_captcha: bool = False


class QuestResult(BaseModel):
    """Outcome of a quest request."""
    outcome: bool = True
    gold: int = 0
    xp: int = 0
    rank: int = 0
    tribe_rank: int = 0
    total_quests: int = 0
    potion: int = 0
    nectar: int = 0
    q: Optional[str] = None
    needs_captcha: bool = False


class CollectGoldResult(BaseModel):
    """Outcome of gold collection request."""
    collected_gold: int = 0
    player_gold: int = 0
    gold_collection_allowed: bool = False
    gold_collection_allowed_at: Optional[int] = None
    gold_collection_extraction: int = 0
    last_gold_collected_at: Optional[int] = None
    needs_captcha: bool = False


class TribeMember(BaseModel):
    """Tribe member representation."""
    id: str = ""
    name: str = ""
    rank: int = 0
    xp: int = 0
    gold: int = 0
    permission: int = 0
    level: int = 1
    def_power: int = 0
    league: int = 0
    avatar: int = 0
    status: str = "active"
