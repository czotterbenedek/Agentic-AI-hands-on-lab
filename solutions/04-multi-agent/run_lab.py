"""Runnable demonstration for Module 4: Multi-Agent Systems & Handoff."""

import os
import sys

module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from orchestrator import MultiAgentOrchestrator


def main() -> None:
    print("=" * 70)
    print("🎓 BME MSc AI in Practice - Lab 4: Multi-Agent Delegation & Handoff")
    print("   Central Example: Supervisor + Research Specialist + Analysis Specialist")
    print("=" * 70)

    orchestrator = MultiAgentOrchestrator()

    query = "Investigate parameter-efficient fine-tuning and compare LoRA with standard Transformers"
    print(f"\nUser Research Query:\n{query}\n")

    context = orchestrator.execute_workflow(query)

    print("\n" + "=" * 30 + " Execution Trace " + "=" * 30)
    for step, hop in enumerate(context.get_trace_summary(), 1):
        print(f"Step {step}: {hop}")

    print("\n" + "=" * 30 + " Final Synthesized Report " + "=" * 30)
    print(context.final_synthesis)


if __name__ == "__main__":
    main()
