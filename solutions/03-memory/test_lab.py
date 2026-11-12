"""Unit and integration tests for Module 3: Persistent Agent Memory."""

import os
import sys

try:
    import pytest
except ImportError:
    pytest = None

module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from storage import SQLiteMemoryStorage
from memory_manager import MemoryManager
from memory_agent import MemoryAugmentedAgent

TEST_DB = os.path.join(module_dir, "pytest_memory.db")


def setup_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def teardown_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_sqlite_table_initialization():
    """Verify SQLite database schema tables are created."""
    storage = SQLiteMemoryStorage(db_path=TEST_DB)
    with storage._get_connection() as conn:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
    assert "conversations" in tables
    assert "user_preferences" in tables
    assert "research_notes" in tables


def test_preference_crud():
    """Verify preference insert, update, retrieval, and deletion."""
    storage = SQLiteMemoryStorage(db_path=TEST_DB)
    storage.save_preference("alice", "research_topic", "diffusion models")
    prefs = storage.get_preferences("alice")
    assert prefs.get("research_topic") == "diffusion models"

    # Update preference
    storage.save_preference("alice", "research_topic", "llm reasoning")
    prefs = storage.get_preferences("alice")
    assert prefs.get("research_topic") == "llm reasoning"

    # Delete preference
    deleted = storage.delete_preference("alice", "research_topic")
    assert deleted is True
    assert "research_topic" not in storage.get_preferences("alice")


def test_user_memory_isolation():
    """Verify that user A cannot see or contaminate user B's preferences or notes."""
    storage = SQLiteMemoryStorage(db_path=TEST_DB)
    storage.save_preference("alice", "interest", "robotics")
    storage.save_preference("bob", "interest", "quantum computing")

    storage.save_note("alice", "plan", "Alice's secret thesis notes")

    alice_prefs = storage.get_preferences("alice")
    bob_prefs = storage.get_preferences("bob")

    assert alice_prefs["interest"] == "robotics"
    assert bob_prefs["interest"] == "quantum computing"

    alice_notes = storage.get_notes("alice")
    bob_notes = storage.get_notes("bob")

    assert len(alice_notes) == 1
    assert len(bob_notes) == 0


def test_conversation_history_persistence():
    """Verify storing and retrieving conversation history."""
    storage = SQLiteMemoryStorage(db_path=TEST_DB)
    storage.save_message("alice", "sess_1", "user", "Hello Assistant")
    storage.save_message("alice", "sess_1", "assistant", "Hello Alice! How can I help?")

    history = storage.get_conversation_history("alice", "sess_1")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_memory_prompt_injection():
    """Verify formatting of persistent preferences into system prompt context."""
    storage = SQLiteMemoryStorage(db_path=TEST_DB)
    storage.save_preference("alice", "topic", "Transformer Efficiency")
    storage.save_note("alice", "idea", "Evaluate 4-bit quantization")

    manager = MemoryManager(storage=storage)
    context = manager.get_system_context("alice")

    assert "Transformer Efficiency" in context
    assert "Evaluate 4-bit quantization" in context


def test_clear_user_data():
    """Verify memory wipe completely cleans user data."""
    storage = SQLiteMemoryStorage(db_path=TEST_DB)
    storage.save_preference("alice", "topic", "LoRA")
    storage.save_note("alice", "tag", "note1")
    storage.save_message("alice", "s1", "user", "test")

    storage.clear_user_data("alice")

    assert len(storage.get_preferences("alice")) == 0
    assert len(storage.get_notes("alice")) == 0
    assert len(storage.get_conversation_history("alice", "s1")) == 0


if __name__ == "__main__":
    setup_function()
    tests = [
        test_sqlite_table_initialization,
        test_preference_crud,
        test_user_memory_isolation,
        test_conversation_history_persistence,
        test_memory_prompt_injection,
        test_clear_user_data,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✓ {t.__name__} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__} FAILED: {e}")
    teardown_function()
    print(f"\n{passed}/{len(tests)} tests passed.")
    if passed != len(tests):
        sys.exit(1)
