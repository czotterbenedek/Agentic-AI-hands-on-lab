"""Runnable demonstration for Module 5: Agent Evaluation Framework (Starter Lab)."""

import os
import sys

module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from evaluator import AgentEvaluator


def main() -> None:
    print("=" * 75)
    print("🎓 BME MSc AI in Practice - Lab 5: Systematic Agent Evaluation")
    print("   Benchmarking 4 Agent Configurations on University Research Assistant (Starter Lab)")
    print("=" * 75)

    try:
        evaluator = AgentEvaluator()
        print(f"\nLoaded {len(evaluator.test_cases)} benchmark test cases.")
        print("Running evaluation across 4 configurations...\n")

        results = evaluator.run_all()

        print("\n" + "=" * 75)
        print("📊 COMPARATIVE EVALUATION RESULTS SUMMARY")
        print("=" * 75)
        print(f"{'Configuration':<28} | {'Success Rate':<13} | {'Tool F1':<8} | {'Steps':<8} | {'Latency':<8}")
        print("-" * 75)
        for row in results["summary"]:
            print(
                f"{row['Configuration']:<28} | {row['Success Rate']:<13} | "
                f"{row['Tool F1 Score']:<8} | {row['Avg Steps']:<8} | {row['Avg Latency (s)']:<8}"
            )
        print("=" * 75)

        out_prefix = os.path.join(module_dir, "evaluation_benchmark")
        evaluator.export_results(results, output_prefix=out_prefix)
        print(f"\n💾 Results exported to {out_prefix}.csv and {out_prefix}.json\n")

    except NotImplementedError as e:
        print(f"\n[TODO Required]: {e}")


if __name__ == "__main__":
    main()
