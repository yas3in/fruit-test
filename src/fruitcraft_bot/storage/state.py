"""SQLite persistence engine for FruitCraft Bot history and account states."""

import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fruitcraft.storage.state")


class StateDatabase:
    """Synchronous / Async SQLite storage manager for statistics, snapshots, and logs."""

    def __init__(self, db_path: str = "fruitcraft.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database schema tables if not present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # accounts table (NO plaintext passwords or restore keys)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    name TEXT,
                    level INTEGER DEFAULT 1,
                    gold INTEGER DEFAULT 0,
                    state TEXT DEFAULT 'DISCONNECTED',
                    updated_at INTEGER
                )
            """)

            # player_snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS player_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    level INTEGER,
                    gold INTEGER,
                    nectar INTEGER,
                    potion INTEGER,
                    rank INTEGER,
                    league INTEGER,
                    timestamp INTEGER
                )
            """)

            # battle_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS battle_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    opponent_id TEXT,
                    opp_name TEXT,
                    won INTEGER,
                    gold_earned INTEGER,
                    xp_earned INTEGER,
                    timestamp INTEGER
                )
            """)

            # quest_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quest_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    outcome INTEGER,
                    gold INTEGER,
                    xp INTEGER,
                    potion INTEGER,
                    nectar INTEGER,
                    timestamp INTEGER
                )
            """)

            # gold_collection_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gold_collection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    collected_gold INTEGER,
                    player_gold INTEGER,
                    timestamp INTEGER
                )
            """)

            # card_actions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS card_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    action_type TEXT,
                    details TEXT,
                    timestamp INTEGER
                )
            """)

            # errors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    endpoint TEXT,
                    code INTEGER,
                    message TEXT,
                    timestamp INTEGER
                )
            """)

            # worker_runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS worker_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    worker_type TEXT,
                    state TEXT,
                    items_processed INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    started_at INTEGER,
                    stopped_at INTEGER
                )
            """)

            conn.commit()

    def record_account_state(self, account_id: str, name: str, level: int, gold: int, state: str):
        """Record or update account state metadata."""
        now = int(time.time())
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO accounts (account_id, name, level, gold, state, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                    name=excluded.name,
                    level=excluded.level,
                    gold=excluded.gold,
                    state=excluded.state,
                    updated_at=excluded.updated_at
            """, (account_id, name, level, gold, state, now))
            conn.commit()

    def record_battle(self, account_id: str, opponent_id: str, opp_name: str, won: bool, gold: int, xp: int):
        """Log battle outcome."""
        now = int(time.time())
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO battle_history (account_id, opponent_id, opp_name, won, gold_earned, xp_earned, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (account_id, opponent_id, opp_name, 1 if won else 0, gold, xp, now))
            conn.commit()

    def record_quest(self, account_id: str, outcome: bool, gold: int, xp: int, potion: int, nectar: int):
        """Log quest completion."""
        now = int(time.time())
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO quest_history (account_id, outcome, gold, xp, potion, nectar, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (account_id, 1 if outcome else 0, gold, xp, potion, nectar, now))
            conn.commit()

    def record_gold_collection(self, account_id: str, collected: int, player_gold: int):
        """Log gold mine collection."""
        now = int(time.time())
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO gold_collection_history (account_id, collected_gold, player_gold, timestamp)
                VALUES (?, ?, ?, ?)
            """, (account_id, collected, player_gold, now))
            conn.commit()

    def record_error(self, account_id: str, endpoint: str, code: int, message: str):
        """Log error entry safely."""
        now = int(time.time())
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO errors (account_id, endpoint, code, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (account_id, endpoint, code, message, now))
            conn.commit()

    def get_stats(self, account_id: str = "default") -> Dict[str, Any]:
        """Fetch summary statistics for account."""
        with self._get_connection() as conn:
            c = conn.cursor()

            c.execute("SELECT COUNT(*), SUM(won), SUM(gold_earned) FROM battle_history WHERE account_id=?", (account_id,))
            b_row = c.fetchone()
            total_battles = b_row[0] or 0
            wins = b_row[1] or 0
            battle_gold = b_row[2] or 0

            c.execute("SELECT COUNT(*), SUM(gold) FROM quest_history WHERE account_id=?", (account_id,))
            q_row = c.fetchone()
            total_quests = q_row[0] or 0
            quest_gold = q_row[1] or 0

            c.execute("SELECT SUM(collected_gold) FROM gold_collection_history WHERE account_id=?", (account_id,))
            g_row = c.fetchone()
            mine_gold = g_row[0] or 0

            return {
                "account_id": account_id,
                "total_battles": total_battles,
                "wins": wins,
                "losses": total_battles - wins,
                "battle_gold": battle_gold,
                "total_quests": total_quests,
                "quest_gold": quest_gold,
                "mine_gold": mine_gold,
                "total_gold_earned": battle_gold + quest_gold + mine_gold,
            }
