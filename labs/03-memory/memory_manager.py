"""Memory manager orchestrating short-term history, long-term persistence, and prompt injection (Starter Lab)."""

from typing import Any, Dict, List, Optional

from shared.agent import Tool
try:
    from .storage import SQLiteMemoryStorage
except ImportError:
    from storage import SQLiteMemoryStorage


class MemoryManager:
    """Manages short-term conversation history and persistent user-isolated memory."""

    def __init__(self, storage: Optional[SQLiteMemoryStorage] = None, max_history_turns: int = 10):
        self.storage = storage or SQLiteMemoryStorage()
        self.max_history_turns = max_history_turns

    def get_system_context(self, user_id: str) -> str:
        """Format persistent user preferences and research notes for injection into agent context.

        # ==============================================================================
        # TODO [Lab 3.4a]: Context Injection Formatting (~30 lines)
        # ------------------------------------------------------------------------------
        # 1. Fetch preferences using `self.storage.get_preferences(user_id)`.
        # 2. Fetch notes using `self.storage.get_notes(user_id)`.
        # 3. If both are empty, return "" (empty string).
        # 4. Construct a structured section header:
        #    [PERSISTENT STUDENT RESEARCH MEMORY]
        #    Student Preferences:
        #      • <Key>: <Value>
        #    Student Research Notes:
        #      • [<Topic>] <Content>
        # 5. Return the formatted multi-line string.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 3.4a]: Implement get_system_context")

    def record_turn(self, user_id: str, session_id: str, role: str, content: str) -> None:
        """Record a conversation turn in persistent storage."""
        self.storage.save_message(user_id, session_id, role, content)

    def get_recent_history(self, user_id: str, session_id: str) -> List[Dict[str, str]]:
        """Retrieve recent conversation history within sliding window limit.

        # ==============================================================================
        # TODO [Lab 3.4b]: Short-Term History Sliding Window (~15 lines)
        # ------------------------------------------------------------------------------
        # Retrieve recent history from `self.storage.get_conversation_history(...)`
        # limited to `self.max_history_turns * 2` messages.
        # Format as list of `{"role": ..., "content": ...}` dictionaries.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 3.4b]: Implement get_recent_history")

    # --------------------------------------------------------------------------
    # Agent Tools for Memory Self-Management
    # --------------------------------------------------------------------------

    def get_memory_tools(self, user_id: str) -> List[Tool]:
        """Return executable Tool instances for agent to save/retrieve user memory.

        # ==============================================================================
        # TODO [Lab 3.5]: Memory Self-Management Tools (~45 lines)
        # ------------------------------------------------------------------------------
        # Build Tool instances allowing the agent to update memory:
        # 1. `save_preference(key: str, value: str)`: calls `storage.save_preference(user_id, key, value)`.
        # 2. `get_preferences()`: calls `storage.get_preferences(user_id)` and returns string.
        # 3. `save_research_note(topic: str, note: str)`: calls `storage.save_note(user_id, topic, note)`.
        # 4. `clear_memory()`: calls `storage.clear_user_data(user_id)`.
        # Return list of Tool objects with schemas.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 3.5]: Implement get_memory_tools")
