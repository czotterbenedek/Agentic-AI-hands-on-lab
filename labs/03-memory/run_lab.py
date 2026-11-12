"""Runnable demonstration for Module 3: Agent Memory & Personalization (Starter Lab)."""

import os
import sys

module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from storage import SQLiteMemoryStorage
from memory_manager import MemoryManager
from memory_agent import MemoryAugmentedAgent


def main() -> None:
    print("=" * 70)
    print("🎓 BME MSc AI in Practice - Lab 3: Persistent Agent Memory")
    print("   Central Example: University Research Assistant with SQLite Memory (Starter Lab)")
    print("=" * 70)

    db_file = os.path.join(module_dir, "test_lab_memory.db")
    if os.path.exists(db_file):
        os.remove(db_file)

    try:
        storage = SQLiteMemoryStorage(db_path=db_file)
        manager = MemoryManager(storage=storage)
        agent = MemoryAugmentedAgent(memory_manager=manager)

        print("\n📝 Scenario 1: Alice establishes research preferences in Session 1")
        agent.run(
            "Please remember that my research topic is parameter-efficient fine-tuning and LoRA.",
            user_id="alice",
            session_id="session_101",
        )

        print("\n🔄 Scenario 2: Alice returns in a NEW session (Session 102)")
        print("System context injected from persistent SQLite memory:")
        print(manager.get_system_context("alice"))
        ans_alice = agent.run(
            "Recommend research papers for my topic.",
            user_id="alice",
            session_id="session_102",
        )
        print(f"\n[Alice Answer]:\n{ans_alice}")

        print("\n🔒 Scenario 3: User Isolation Check - Bob asks the same question")
        print("Bob's system context:")
        bob_context = manager.get_system_context("bob")
        print(bob_context if bob_context else "[No preferences found - isolated!]")
        ans_bob = agent.run(
            "Recommend research papers for my topic.",
            user_id="bob",
            session_id="session_201",
        )
        print(f"\n[Bob Answer]:\n{ans_bob}")

    except NotImplementedError as e:
        print(f"\n[TODO Required]: {e}")
    finally:
        if os.path.exists(db_file):
            os.remove(db_file)


if __name__ == "__main__":
    main()
