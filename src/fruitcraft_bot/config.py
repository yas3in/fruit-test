"""Configuration models and environment loading for FruitCraft Bot."""

import json
import os
from typing import Any, Dict, Optional, Union


def load_env_file():
    """Locate and load .env file from current or parent directories if present."""
    curr = os.getcwd()
    for _ in range(4):
        env_path = os.path.join(curr, ".env")
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'").strip('"')
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass
            break
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent


load_env_file()


try:
    from pydantic import BaseModel, Field, SecretStr
except ImportError:
    from fruitcraft_bot.api.models import BaseModel, Field

    class SecretStr:
        def __init__(self, secret_value: str = ""):
            self._secret_value = str(secret_value)
        def get_secret_value(self) -> str:
            return self._secret_value
        def __repr__(self) -> str:
            return "SecretStr('**********')"
        def __str__(self) -> str:
            return "**********"


DEFAULT_XOR_KEY = "ali1343faraz1055antler288based"
DEFAULT_GAME_VERSION = "1.9.10691"
DEFAULT_BASE_URL = "http://iran.fruitcraft.ir"


class DeviceConfig(BaseModel):
    """Device specification sent in player/load requests."""
    game_version: str = DEFAULT_GAME_VERSION
    udid: str = "0000000000000000"
    os_type: int = 2
    os_version: str = "7.1.2"
    model: str = "google pixel 2"
    metrix_uid: str = "-"
    appsflyer_uid: str = "-"
    device_name: str = "unknown"
    store_type: str = "myket"


class BattleConfig(BaseModel):
    """Configuration options for auto-battle operations."""
    max_battles_per_run: int = 50
    minimum_gold: int = 0
    maximum_def_power_ratio: float = 1.2
    prefer_gold: bool = True
    prefer_low_defense: bool = True
    stop_on_captcha: bool = True
    stop_on_error: bool = True
    strategy: str = "weakest"


class AutomationConfig(BaseModel):
    """Automation execution settings and delays."""
    battle_enabled: bool = True
    quest_enabled: bool = True
    mine_enabled: bool = True

    battle_delay_min: float = 3.0
    battle_delay_max: float = 6.0

    quest_delay_min: float = 4.0
    quest_delay_max: float = 8.0

    auto_heal: bool = False
    auto_potionize: bool = False
    auto_evolve: bool = False
    auto_cooloff: bool = False

    max_battles_per_run: int = 50
    max_quests_per_run: int = 50

    stop_on_captcha: bool = True
    stop_on_error: bool = True

    minimum_gold: int = 0
    maximum_gold_spend: int = 100000


class AccountConfig(BaseModel):
    """Account profile settings."""
    account_id: str = "default"
    restore_key: SecretStr = Field(default_factory=lambda: SecretStr(""))
    passport: Optional[SecretStr] = None
    device: DeviceConfig = Field(default_factory=DeviceConfig)
    battle: BattleConfig = Field(default_factory=BattleConfig)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)


class AppSettings:
    """Global application settings loaded from environment variables."""

    def __init__(self):
        load_env_file()
        self.base_url = os.getenv("FRUITCRAFT_BASE_URL", DEFAULT_BASE_URL)
        self.xor_key = os.getenv("FRUITCRAFT_XOR_KEY", DEFAULT_XOR_KEY)
        key_env = os.getenv("FRUITCRAFT_RESTORE_KEY")
        self.restore_key = SecretStr(key_env) if key_env else None
        self.db_path = os.getenv("FRUITCRAFT_DB_PATH", "fruitcraft.db")
        self.log_level = os.getenv("FRUITCRAFT_LOG_LEVEL", "INFO")
        self.accounts_json = os.getenv("FRUITCRAFT_ACCOUNTS")

    def get_accounts(self) -> Dict[str, AccountConfig]:
        """Parse multi-account configuration or fallback to single account setup."""
        accounts = {}
        if self.accounts_json:
            try:
                data = json.loads(self.accounts_json)
                for acc_id, acc_data in data.items():
                    accounts[acc_id] = AccountConfig(
                        account_id=acc_id,
                        restore_key=SecretStr(acc_data.get("restore_key", "")),
                        passport=SecretStr(acc_data["passport"]) if "passport" in acc_data else None
                    )
            except Exception:
                pass

        if not accounts and self.restore_key:
            accounts["default"] = AccountConfig(
                account_id="default",
                restore_key=self.restore_key
            )

        return accounts
