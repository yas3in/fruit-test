"""SQLAlchemy database models for FruitCraft automation system."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Account(Base):
    """FruitCraft player account."""
    __tablename__ = "accounts"

    id = Column(String(64), primary_key=True, index=True)  # uuid or slug identifier
    name = Column(String(128), nullable=False)             # User-friendly label (e.g. "Main Account")
    restore_key = Column(String(256), nullable=False)      # FruitCraft restore key
    is_active = Column(Boolean, default=True)              # Whether automation is allowed

    # Game data loaded from FruitCraft
    player_id = Column(Integer, nullable=True)
    player_name = Column(String(128), nullable=True)
    avatar_id = Column(Integer, nullable=True)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    nectar = Column(Integer, default=0)
    potion = Column(Integer, default=0)
    global_rank = Column(Integer, nullable=True)
    league_rank = Column(Integer, nullable=True)
    tribe_id = Column(Integer, nullable=True)
    tribe_name = Column(String(128), nullable=True)
    attack_power = Column(Integer, default=0)
    defense_power = Column(Integer, default=0)

    # Operational status
    current_state = Column(String(32), default="STOPPED")  # READY, RUNNING, WAITING, ERROR, CAPTCHA REQUIRED, STOPPED
    battle_worker_status = Column(String(32), default="STOPPED")  # RUNNING, PAUSED, STOPPED, ERROR
    mine_worker_status = Column(String(32), default="STOPPED")
    quest_worker_status = Column(String(32), default="STOPPED")

    last_activity = Column(DateTime, nullable=True)
    next_action = Column(String(256), nullable=True)
    last_error = Column(Text, nullable=True)
    captcha_status = Column(String(32), default="NONE")  # NONE, REQUIRED, SOLVED
    last_successful_request = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    battles = relationship("BattleRecord", back_populates="account", cascade="all, delete-orphan")
    quests = relationship("QuestRecord", back_populates="account", cascade="all, delete-orphan")
    mine_collections = relationship("MineCollectionRecord", back_populates="account", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="account", cascade="all, delete-orphan")
    notifications = relationship("NotificationRecord", back_populates="account", cascade="all, delete-orphan")


class BattleRecord(Base):
    """History of battles fought."""
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    opponent_id = Column(Integer, nullable=True)
    opponent_name = Column(String(128), default="Unknown")
    opponent_power = Column(Integer, default=0)
    result = Column(String(16), nullable=False)  # WIN, LOSS
    gold_earned = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    cards_used = Column(Text, default="[]")       # JSON array of card IDs or names
    duration_ms = Column(Integer, default=0)

    account = relationship("Account", back_populates="battles")


class QuestRecord(Base):
    """History of quests completed."""
    __tablename__ = "quests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    quest_name = Column(String(128), default="Standard Quest")
    result = Column(String(16), default="SUCCESS")
    gold_earned = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    cards_used = Column(Text, default="[]")

    account = relationship("Account", back_populates="quests")


class MineCollectionRecord(Base):
    """History of gold mine collections."""
    __tablename__ = "mine_collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    gold_collected = Column(Integer, default=0)

    account = relationship("Account", back_populates="mine_collections")


class ActivityLog(Base):
    """Activity feed events."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=True)
    account_name = Column(String(128), default="System")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    event_type = Column(String(64), nullable=False, index=True)
    message = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")

    account = relationship("Account", back_populates="activities")


class NotificationRecord(Base):
    """System notifications with deduplication and priority levels."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=True)
    account_name = Column(String(128), default="System")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    priority = Column(String(16), default="INFO", index=True)  # INFO, WARNING, ERROR, CRITICAL
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    deduplication_key = Column(String(256), index=True, nullable=True)
    occurrence_count = Column(Integer, default=1)
    last_occurrence = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_read = Column(Boolean, default=False)

    account = relationship("Account", back_populates="notifications")


class SystemSetting(Base):
    """Dynamic key-value settings stored in DB."""
    __tablename__ = "system_settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=False)  # JSON-encoded value
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DailyReport(Base):
    """Aggregated daily statistics."""
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_str = Column(String(32), index=True, nullable=False)  # YYYY-MM-DD
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    battles_count = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    gold_earned = Column(Integer, default=0)
    quests_count = Column(Integer, default=0)
    mine_collections = Column(Integer, default=0)
    cards_upgraded = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    runtime_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
