"""SQLite persistent memory storage engine with user isolation (Starter Lab)."""

import os
import sqlite3
import time
from typing import Any, Dict, List, Optional


class SQLiteMemoryStorage:
    """Persistent storage engine using SQLite for conversations, preferences, and notes."""

    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return an SQLite connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create database tables if they do not exist.

        # ==============================================================================
        # TODO [Lab 3.1]: Initialize SQLite Database Schema (~45 lines)
        # ------------------------------------------------------------------------------
        # Create three tables using `self._get_connection()`:
        #
        # 1. `conversations`:
        #    - id: INTEGER PRIMARY KEY AUTOINCREMENT
        #    - user_id: TEXT NOT NULL
        #    - session_id: TEXT NOT NULL
        #    - role: TEXT NOT NULL
        #    - content: TEXT NOT NULL
        #    - created_at: REAL NOT NULL
        #    - Index on (user_id, session_id)
        #
        # 2. `user_preferences`:
        #    - user_id: TEXT NOT NULL
        #    - pref_key: TEXT NOT NULL
        #    - pref_value: TEXT NOT NULL
        #    - updated_at: REAL NOT NULL
        #    - PRIMARY KEY (user_id, pref_key) -> ensures one value per user per key!
        #
        # 3. `research_notes`:
        #    - id: INTEGER PRIMARY KEY AUTOINCREMENT
        #    - user_id: TEXT NOT NULL
        #    - topic: TEXT NOT NULL
        #    - content: TEXT NOT NULL
        #    - created_at: REAL NOT NULL
        #    - Index on (user_id, topic)
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 3.1]: Implement _init_db")

    # --------------------------------------------------------------------------
    # Conversation History Methods
    # --------------------------------------------------------------------------

    def save_message(self, user_id: str, session_id: str, role: str, content: str) -> None:
        """Save a single conversation message."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (user_id, session_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, session_id, role, content, time.time()),
            )
            conn.commit()

    def get_conversation_history(
        self, user_id: str, session_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve recent conversation history for a specific user and session."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT role, content, created_at
                FROM conversations
                WHERE user_id = ? AND session_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (user_id, session_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --------------------------------------------------------------------------
    # Long-term User Preferences Methods (User Isolated)
    # --------------------------------------------------------------------------

    def save_preference(self, user_id: str, key: str, value: str) -> None:
        """Insert or update a user-specific preference.

        # ==============================================================================
        # TODO [Lab 3.2a]: Save User Preference (~20 lines)
        # ------------------------------------------------------------------------------
        # 1. Clean key (strip and lowercase) and value (strip string).
        # 2. Insert into `user_preferences (user_id, pref_key, pref_value, updated_at)`.
        # 3. Use `ON CONFLICT(user_id, pref_key) DO UPDATE SET pref_value = excluded.pref_value,
        #    updated_at = excluded.updated_at` (Upsert).
        # 4. Commit transaction.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 3.2a]: Implement save_preference")

    def get_preferences(self, user_id: str) -> Dict[str, str]:
        """Retrieve all preferences stored for a specific user.

        # ==============================================================================
        # TODO [Lab 3.2b]: Get User Preferences with Strict Isolation (~15 lines)
        # ------------------------------------------------------------------------------
        # 1. Query `SELECT pref_key, pref_value FROM user_preferences WHERE user_id = ?`.
        # 2. Return dictionary mapping `pref_key -> pref_value`.
        # 3. CRITICAL: Never return preferences of any other user!
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 3.2b]: Implement get_preferences")

    def delete_preference(self, user_id: str, key: str) -> bool:
        """Delete a single preference for a user.

        # ==============================================================================
        # TODO [Lab 3.2c]: Delete Preference (~15 lines)
        # ------------------------------------------------------------------------------
        # 1. Execute `DELETE FROM user_preferences WHERE user_id = ? AND pref_key = ?`.
        # 2. Return True if a row was deleted (cursor.rowcount > 0), else False.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 3.2c]: Implement delete_preference")

    # --------------------------------------------------------------------------
    # Research Notes Methods
    # --------------------------------------------------------------------------

    def save_note(self, user_id: str, topic: str, content: str) -> int:
        """Save a research note under a topic."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO research_notes (user_id, topic, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, topic.strip().lower(), content.strip(), time.time()),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_notes(self, user_id: str, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve notes for a user, optionally filtered by topic."""
        with self._get_connection() as conn:
            if topic:
                cursor = conn.execute(
                    """
                    SELECT id, topic, content, created_at
                    FROM research_notes
                    WHERE user_id = ? AND topic = ?
                    ORDER BY id DESC
                    """,
                    (user_id, topic.strip().lower()),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, topic, content, created_at
                    FROM research_notes
                    WHERE user_id = ?
                    ORDER BY id DESC
                    """,
                    (user_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    # --------------------------------------------------------------------------
    # Inspection and Cleanup
    # --------------------------------------------------------------------------

    def inspect_memory(self, user_id: str) -> Dict[str, Any]:
        """Inspect all stored memory records for a given user."""
        return {
            "user_id": user_id,
            "preferences": self.get_preferences(user_id),
            "notes": self.get_notes(user_id),
        }

    def clear_user_data(self, user_id: str) -> None:
        """Permanently delete all conversation history, preferences, and notes for a user.

        # ==============================================================================
        # TODO [Lab 3.3]: Clear User Memory Data (~20 lines)
        # ------------------------------------------------------------------------------
        # Execute DELETE FROM for `conversations`, `user_preferences`, and `research_notes`
        # for the given `user_id`. Do not delete records of any other user!
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 3.3]: Implement clear_user_data")
