"""Auto-battle worker and account state machine."""

import asyncio
import logging
import random
import time
from enum import Enum
from typing import Dict, Optional

from fruitcraft_bot.api.errors import CaptchaRequiredError, FruitCraftError
from fruitcraft_bot.config import AccountConfig, BattleConfig
from fruitcraft_bot.services.auth import AuthService
from fruitcraft_bot.services.battle import BattleService, STRATEGY_MAP
from fruitcraft_bot.services.cards import CardService, StrongestCardsStrategy
from fruitcraft_bot.services.player import PlayerService
from fruitcraft_bot.storage.state import StateDatabase

logger = logging.getLogger("fruitcraft.automation.battle")


class AccountState(str, Enum):
    """Explicit account state machine values."""
    DISCONNECTED = "DISCONNECTED"
    AUTHENTICATING = "AUTHENTICATING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    ERROR = "ERROR"
    STOPPED = "STOPPED"


class BattleWorker:
    """Automated battle worker loop with state tracking."""

    def __init__(
        self,
        account_config: AccountConfig,
        auth_service: AuthService,
        player_service: PlayerService,
        battle_service: BattleService,
        card_service: CardService,
        db: Optional[StateDatabase] = None,
    ):
        self.config = account_config
        self.battle_cfg = account_config.battle
        self.auto_cfg = account_config.automation
        self.auth = auth_service
        self.player = player_service
        self.battle = battle_service
        self.cards = card_service
        self.db = db or StateDatabase()

        self.state: AccountState = AccountState.DISCONNECTED
        self._running = False

        # Metrics
        self.total_battles = 0
        self.wins = 0
        self.losses = 0
        self.gold_earned = 0
        self.xp_earned = 0
        self.errors_count = 0

    def _set_state(self, new_state: AccountState):
        logger.info("[%s] State transition: %s -> %s", self.config.account_id, self.state, new_state)
        self.state = new_state
        if self.auth.player_info:
            self.db.record_account_state(
                account_id=self.config.account_id,
                name=self.auth.player_info.name,
                level=self.auth.player_info.level,
                gold=self.auth.player_info.gold,
                state=self.state.value,
            )

    def stop(self):
        """Signal worker loop to stop."""
        self._running = False
        if self.state not in (AccountState.CAPTCHA_REQUIRED, AccountState.ERROR):
            self._set_state(AccountState.STOPPED)

    async def run(self):
        """Execute main battle automation loop."""
        self._running = True

        # Phase 1: Authentication
        self._set_state(AccountState.AUTHENTICATING)
        try:
            await self.auth.load_player(self.config.restore_key, self.config.device)
            self._set_state(AccountState.READY)
        except CaptchaRequiredError:
            self._set_state(AccountState.CAPTCHA_REQUIRED)
            logger.warning("[%s] CAPTCHA required during load. Stopping battle worker.", self.config.account_id)
            return
        except Exception as e:
            self._set_state(AccountState.ERROR)
            logger.error("[%s] Auth failed: %s", self.config.account_id, e)
            return

        battles_run = 0

        while self._running and battles_run < self.auto_cfg.max_battles_per_run:
            self._set_state(AccountState.RUNNING)

            try:
                # 1. Fetch available opponents
                opponents = await self.battle.get_opponents()
                if not opponents:
                    logger.warning("[%s] No opponents found. Waiting...", self.config.account_id)
                    self._set_state(AccountState.WAITING)
                    await asyncio.sleep(5.0)
                    continue

                # 2. Select opponent according to configured strategy
                strategy = STRATEGY_MAP.get(self.battle_cfg.strategy.lower(), STRATEGY_MAP["weakest"])
                target_opp = strategy.select_opponent(opponents, self.battle_cfg)

                if not target_opp:
                    logger.warning("[%s] Strategy failed to select an opponent.", self.config.account_id)
                    await asyncio.sleep(5.0)
                    continue

                # 3. Select strongest cards
                available_cards = self.auth.player_info.cards if self.auth.player_info else []
                card_sel = StrongestCardsStrategy().select(available_cards, count=4)
                if not card_sel.cards:
                    logger.warning("[%s] No valid cards found in player profile to battle with.", self.config.account_id)
                    await asyncio.sleep(5.0)
                    continue

                # 4. Execute battle
                result = await self.battle.battle(
                    opponent_id=target_opp.id,
                    cards=card_sel.cards,
                    hero_id=card_sel.hero_id,
                )

                # 5. Process and record result
                self.total_battles += 1
                battles_run += 1
                if result.won:
                    self.wins += 1
                else:
                    self.losses += 1

                self.gold_earned += result.gold_earned
                self.xp_earned += result.xp_earned

                self.db.record_battle(
                    account_id=self.config.account_id,
                    opponent_id=target_opp.id,
                    opp_name=target_opp.name or result.opp_name,
                    won=result.won,
                    gold=result.gold_earned,
                    xp=result.xp_earned,
                )

                if result.needs_captcha:
                    self._set_state(AccountState.CAPTCHA_REQUIRED)
                    logger.warning("[%s] CAPTCHA requested during battle. Halting worker.", self.config.account_id)
                    self._running = False
                    break

                # 6. Auto-heal damaged cards if configured
                if self.auto_cfg.auto_heal and result.cards_damaged:
                    await self.cards.heal_all(result.cards_damaged, max_gold_spend=self.auto_cfg.maximum_gold_spend)

                # 7. Wait randomized delay between actions
                delay = random.uniform(self.auto_cfg.battle_delay_min, self.auto_cfg.battle_delay_max)
                self._set_state(AccountState.WAITING)
                logger.debug("[%s] Waiting %.2fs before next battle...", self.config.account_id, delay)
                await asyncio.sleep(delay)

            except CaptchaRequiredError:
                self._set_state(AccountState.CAPTCHA_REQUIRED)
                logger.warning("[%s] CAPTCHA Required! Automation paused.", self.config.account_id)
                self._running = False
                break

            except FruitCraftError as e:
                self.errors_count += 1
                self.db.record_error(self.config.account_id, e.endpoint or "battle", e.code or 0, e.message)
                logger.warning("[%s] Battle error (attempt %d): %s", self.config.account_id, self.errors_count, e)
                if self.errors_count >= 3 and self.auto_cfg.stop_on_error:
                    logger.error("[%s] Too many consecutive battle errors (%d). Stopping.", self.config.account_id, self.errors_count)
                    self._set_state(AccountState.ERROR)
                    self._running = False
                    break
                await asyncio.sleep(5.0)

            except Exception as e:
                self.errors_count += 1
                logger.error("[%s] Unexpected error in battle loop: %s", self.config.account_id, e)
                self._set_state(AccountState.ERROR)
                self._running = False
                break

        if self.state not in (AccountState.CAPTCHA_REQUIRED, AccountState.ERROR):
            self._set_state(AccountState.STOPPED)
        logger.info("[%s] Battle worker finished. Ran %d battles (Wins: %d, Losses: %d, Gold: %d)", self.config.account_id, self.total_battles, self.wins, self.losses, self.gold_earned)
