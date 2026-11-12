"""Memory manager orchestrating short-term history, long-term persistence, and prompt injection."""

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
        """Format persistent user preferences and research notes for injection into agent context."""
        prefs = self.storage.get_preferences(user_id)
        notes = self.storage.get_notes(user_id)

        if not prefs and not notes:
            return ""

        lines = ["[PERSISTENT STUDENT RESEARCH MEMORY]"]
        if prefs:
            lines.append("Student Preferences:")
            for k, v in prefs.items():
                lines.append(f"  • {k.replace('_', ' ').title()}: {v}")

        if notes:
            lines.append("Student Research Notes:")
            for n in notes[:5]:
                lines.append(f"  • [{n['topic'].title()}] {n['content']}")

        lines.append("Use these personalized preferences to tailor recommendations and responses.")
        return "\n".join(lines)

    def record_turn(self, user_id: str, session_id: str, role: str, content: str) -> None:
        """Record a conversation turn in persistent storage."""
        self.storage.save_message(user_id, session_id, role, content)

    def get_recent_history(self, user_id: str, session_id: str) -> List[Dict[str, str]]:
        """Retrieve recent conversation history within sliding window limit."""
        history = self.storage.get_conversation_history(
            user_id, session_id, limit=self.max_history_turns * 2
        )
        return [{"role": h["role"], "content": h["content"]} for h in history]

    # --------------------------------------------------------------------------
    # Agent Tools for Memory Self-Management
    # --------------------------------------------------------------------------

    def get_memory_tools(self, user_id: str) -> List[Tool]:
        """Return executable Tool instances for agent to save/retrieve user memory."""

        def save_preference(key: str, value: str) -> str:
            """Save a persistent student preference, e.g. research_interest or preferred_model."""
            self.storage.save_preference(user_id, key, value)
            return f"Preference '{key}' successfully saved as '{value}' for user {user_id}."

        def get_preferences() -> str:
            """Retrieve all stored preferences for the current student."""
            prefs = self.storage.get_preferences(user_id)
            return str(prefs) if prefs else "No preferences currently stored."

        def save_research_note(topic: str, note: str) -> str:
            """Save a persistent academic note under a given topic."""
            nid = self.storage.save_note(user_id, topic, note)
            return f"Note #{nid} on topic '{topic}' saved successfully."

        def clear_memory() -> str:
            """Clear all stored preferences, notes, and conversation history for the current user."""
            self.storage.clear_user_data(user_id)
            return f"All memory records cleared for user {user_id}."

        return [
            Tool(
                name="save_preference",
                description="Save a persistent user preference or research interest.",
                parameters={
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Preference key name, e.g. 'research_topic'"},
                        "value": {"type": "string", "description": "Preference value string"},
                    },
                    "required": ["key", "value"],
                },
                func=save_preference,
            ),
            Tool(
                name="get_preferences",
                description="Get all persistent preferences and research interests of the current student.",
                parameters={"type": "object", "properties": {}},
                func=get_preferences,
            ),
            Tool(
                name="save_research_note",
                description="Save an academic research note or hypothesis under a topic.",
                parameters={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Subject or topic name"},
                        "note": {"type": "string", "description": "Content of the note"},
                    },
                    "required": ["topic", "note"],
                },
                func=save_research_note,
            ),
            Tool(
                name="clear_memory",
                description="Permanently delete all stored memories and history for the current user.",
                parameters={"type": "object", "properties": {}},
                func=clear_memory,
            ),
        ]
