"""Runnable demonstration for Module 1: Tool Calling and ReAct Agent."""

import os
import sys

# Add module directory and project root to sys.path
module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from react_agent import ReActAgent
from tools import get_default_tool_registry


def main() -> None:
    print("=" * 70)
    print("🎓 BME MSc AI in Practice - Lab 1: Tool Calling & ReAct Agent")
    print("   Central Example: University Research Assistant")
    print("=" * 70)

    agent = ReActAgent(tool_registry=get_default_tool_registry())

    queries = [
        "What is 125000 / 5 + 450 * 2?",
        "Find academic research papers on parameter-efficient fine-tuning and LoRA.",
        "Search papers for transformer and calculate average citations.",
    ]

    for idx, query in enumerate(queries, 1):
        print(f"\n{'='*25} Scenario {idx} {'='*25}")
        print(f"User Query: {query}\n")
        answer = agent.run(query)
        print(f"\n[Result]:\n{answer}\n")


if __name__ == "__main__":
    main()
