"""Core application configuration and settings."""

from typing import Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    db_url: str = Field(default="sqlite+aiosqlite:///fruitcraft.db", alias="DATABASE_URL")

    # Security & Auth
    secret_key: SecretStr = Field(default=SecretStr("fruitcraft-super-secret-key-change-in-production"), alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 24 * 7, alias="ACCESS_TOKEN_EXPIRE_MINUTES")  # 7 days
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin123", alias="ADMIN_PASSWORD")

    # Connection & Proxy (Default port 10501)
    proxy_enabled: bool = Field(default=True, alias="PROXY_ENABLED")
    proxy_url: str = Field(default="http://127.0.0.1:10501", alias="PROXY_URL")
    proxy_port: int = Field(default=10501, alias="PROXY_PORT")

    # FruitCraft API
    base_url: str = Field(default="http://iran.fruitcraft.ir", alias="FRUITCRAFT_BASE_URL")
    game_version: str = Field(default="1.10.10744", alias="FRUITCRAFT_GAME_VERSION")
    api_timeout: int = Field(default=20, alias="API_TIMEOUT")
    api_max_attempts: int = Field(default=4, alias="API_MAX_ATTEMPTS")

    # Automation defaults
    battle_delay_min: float = Field(default=3.0, alias="BATTLE_DELAY_MIN")
    battle_delay_max: float = Field(default=6.0, alias="BATTLE_DELAY_MAX")
    max_battles_per_run: int = Field(default=50, alias="MAX_BATTLES_PER_RUN")
    min_gold_threshold: int = Field(default=1000, alias="MIN_GOLD_THRESHOLD")
    max_opponent_defense: int = Field(default=100000, alias="MAX_OPPONENT_DEFENSE")
    auto_heal: bool = Field(default=True, alias="AUTO_HEAL")
    auto_cooldown: bool = Field(default=True, alias="AUTO_COOLDOWN")

    mine_delay_minutes: int = Field(default=30, alias="MINE_DELAY_MINUTES")
    quest_delay_min: float = Field(default=4.0, alias="QUEST_DELAY_MIN")
    quest_delay_max: float = Field(default=8.0, alias="QUEST_DELAY_MAX")
    max_quests_per_run: int = Field(default=30, alias="MAX_QUESTS_PER_RUN")

    # Workers policy & Health Monitor
    auto_restart_workers: bool = Field(default=True, alias="AUTO_RESTART_WORKERS")
    health_check_interval_seconds: int = Field(default=30, alias="HEALTH_CHECK_INTERVAL_SECONDS")
    stop_on_captcha: bool = Field(default=True, alias="STOP_ON_CAPTCHA")
    stop_on_error: bool = Field(default=False, alias="STOP_ON_ERROR")

    # Telegram Notification Service
    telegram_bot_token: Optional[SecretStr] = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, alias="TELEGRAM_CHAT_ID")
    telegram_enabled: bool = Field(default=False, alias="TELEGRAM_ENABLED")

    # Reporting & Timezone
    timezone: str = Field(default="Asia/Tehran", alias="TIMEZONE")
    daily_report_time: str = Field(default="00:00", alias="DAILY_REPORT_TIME")
    logging_level: str = Field(default="INFO", alias="LOGGING_LEVEL")


settings = Settings()
