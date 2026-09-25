"""Auto-quest worker loop with state machine integration."""

import asyncio
import logging
import random
from typing import Optional

from fruitcraft_bot.api.errors import CaptchaRequiredError, FruitCraftError
from fruitcraft_bot.automation.battle_worker import AccountState
from fruitcraft_bot.config import AccountConfig
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.cards import CardService, StrongestCardsStrategy
from fruitcraft_bot.services.quest import QuestService
from fruitcraft_bot.storage.state import StateDatabase

logger = logging.getLogger("fruitcraft.automation.quest")


class QuestWorker:
    """Automated quest worker loop."""

    def __init__(
        self,
        account_config: AccountConfig,
        auth_service: AuthService,
        quest_service: QuestService,
        card_service: CardService,
        db: Optional[StateDatabase] = None,
    ):
        self.config = account_config
        self.auto_cfg = account_config.automation
        self.auth = auth_service
        self.quest = quest_service
        self.cards = card_service
        self.db = db or StateDatabase()

        self.state: AccountState = AccountState.DISCONNECTED
        self._running = False

        self.total_quests = 0
        self.gold_earned = 0
        self.xp_earned = 0
        self.potions_earned = 0
        self.errors_count = 0

    def stop(self):
        """Stop worker execution."""
        self._running = False

    async def run(self):
        """Execute quest loop."""
        self._running = True

        if not self.auth.player_info:
            try:
                await self.auth.load_player(self.config.restore_key, self.config.device)
            except Exception as e:
                logger.error("[%s] Auth load failed for quest worker: %s", self.config.account_id, e)
                return

        quests_run = 0

        while self._running and quests_run < self.auto_cfg.max_quests_per_run:
            try:
                # 1. Select cards for quest
                available_cards = self.auth.player_info.cards if self.auth.player_info else []
                card_sel = StrongestCardsStrategy().select(available_cards, count=4)
                if not card_sel.cards:
                    logger.warning("[%s] No valid cards found in player profile to perform quest.", self.config.account_id)
                    await asyncio.sleep(5.0)
                    continue

                # 2. Execute quest
                result = await self.quest.do_quest(cards=card_sel.cards)

                quests_run += 1
                self.total_quests += 1
                self.gold_earned += result.gold
                self.xp_earned += result.xp
                self.potions_earned += result.potion

                self.db.record_quest(
                    account_id=self.config.account_id,
                    outcome=result.outcome,
                    gold=result.gold,
                    xp=result.xp,
                    potion=result.potion,
                    nectar=result.nectar,
                )

                if result.needs_captcha:
                    logger.warning("[%s] CAPTCHA required in quest worker. Halting.", self.config.account_id)
                    self._running = False
                    break

                # 3. Wait randomized interval
                delay = random.uniform(self.auto_cfg.quest_delay_min, self.auto_cfg.quest_delay_max)
                await asyncio.sleep(delay)

            except CaptchaRequiredError:
                logger.warning("[%s] CAPTCHA required! Quest worker stopped.", self.config.account_id)
                self._running = False
                break

            except FruitCraftError as e:
                self.errors_count += 1
                self.db.record_error(self.config.account_id, e.endpoint or "quest", e.code or 0, e.message)
                logger.warning("[%s] Quest error (attempt %d): %s", self.config.account_id, self.errors_count, e)
                if self.errors_count >= 3 and self.auto_cfg.stop_on_error:
                    logger.error("[%s] Too many consecutive quest errors (%d). Stopping.", self.config.account_id, self.errors_count)
                    self._running = False
                    break
                await asyncio.sleep(5.0)

            except Exception as e:
                self.errors_count += 1
                logger.error("[%s] Error in quest worker: %s", self.config.account_id, e)
                self._running = False
                break

        logger.info("[%s] Quest worker finished. Total quests: %d, Gold: %d, Potions: %d", self.config.account_id, self.total_quests, self.gold_earned, self.potions_earned)
