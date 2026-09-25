"""Ranking service for global, league, and tribe leaderboards."""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from fruitcraft_bot.api.models import BaseModel, Field

from fruitcraft_bot.api.client import FruitCraftAPIClient

logger = logging.getLogger("fruitcraft.services.rankings")


class RankSnapshot(BaseModel):
    """Historical ranking entry."""
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    player_rank: int = Field(default=0)
    league_rank: int = Field(default=0)
    weekly_score: int = Field(default=0)
    tribe_rank: int = Field(default=0)


class RankingService:
    """Manages leaderboard queries and snapshot history."""

    def __init__(self, api_client: FruitCraftAPIClient, history_path: str = "data/rank_history.json"):
        self.client = api_client
        self.history_path = history_path

    async def get_global_rankings(self) -> Dict[str, Any]:
        """Fetch global rankings leaderboard (POST ranking/global)."""
        logger.info("Fetching global rankings...")
        resp = await self.client.request("ranking/global", {})
        return resp.data if isinstance(resp.data, dict) else {"list": resp.data}

    async def get_league_rankings(self) -> Dict[str, Any]:
        """Fetch league rankings leaderboard (POST ranking/league)."""
        logger.info("Fetching league rankings...")
        resp = await self.client.request("ranking/league", {})
        return resp.data if isinstance(resp.data, dict) else {"list": resp.data}

    async def get_tribe_rankings(self) -> Dict[str, Any]:
        """Fetch tribe rankings leaderboard (POST ranking/tribe)."""
        logger.info("Fetching tribe rankings...")
        resp = await self.client.request("ranking/tribe", {})
        return resp.data if isinstance(resp.data, dict) else {"list": resp.data}

    def save_snapshot(self, snapshot: RankSnapshot):
        """Append historical rank snapshot to JSON file."""
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        history = []
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.append(snapshot.model_dump())
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        logger.info("Saved rank snapshot to %s", self.history_path)
