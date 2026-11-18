"""Unit and integration tests for Module 5: Agent Evaluation Framework."""

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

from metrics import (
    compute_task_success,
    compute_tool_selection_accuracy,
    compute_tool_execution_success,
    compute_efficiency,
)
from evaluator import AgentEvaluator


def test_task_success_metric():
    """Verify keyword presence and forbidden keyword detection."""
    assert compute_task_success("The result is 25900.", required_keywords=["25900"]) is True
    assert compute_task_success("Error evaluating code", required_keywords=["25900"]) is False
    assert compute_task_success(
        "Result is 25900 with an error occurred",
        required_keywords=["25900"],
        forbidden_keywords=["error"],
    ) is False


def test_tool_selection_accuracy():
    """Verify precision, recall, and F1 calculations."""
    acc = compute_tool_selection_accuracy(
        expected_tools=["calculate", "search_papers"],
        actual_tools=["calculate", "search_papers"],
    )
    assert acc["f1"] == 1.0
    assert acc["precision"] == 1.0
    assert acc["recall"] == 1.0

    # Partial match
    partial = compute_tool_selection_accuracy(
        expected_tools=["calculate", "search_papers"],
        actual_tools=["calculate"],
    )
    assert partial["precision"] == 1.0
    assert partial["recall"] == 0.5
    assert partial["f1"] == 0.6667


def test_tool_execution_success():
    """Verify execution success rate computation."""
    assert compute_tool_execution_success(["result: 100", "papers: [..]"]) == 1.0
    assert compute_tool_execution_success(["result: 100", "Error: tool failed"]) == 0.5


def test_efficiency_metric():
    """Verify latency and token estimation calculations."""
    eff = compute_efficiency(step_count=3, latency_seconds=1.234)
    assert eff["step_count"] == 3
    assert eff["latency_seconds"] == 1.234
    assert eff["token_estimate"] == 360


def test_evaluator_harness():
    """Verify evaluator runs and generates summary metrics."""
    evaluator = AgentEvaluator()
    assert len(evaluator.test_cases) == 20
    assert len(evaluator.configurations) == 4

    results = evaluator.run_all()
    assert "summary" in results
    assert len(results["summary"]) == 4


def test_mlflow_tracking_logging():
    """Verify MLflow runs are tracked and parameter/metric metadata is recorded."""
    evaluator = AgentEvaluator()
    results = evaluator.run_all()
    # Verify tracker logged all 4 configurations
    assert len(evaluator.local_tracker.runs) == 4
    for run in evaluator.local_tracker.runs:
        assert "config_name" in run["params"]
        assert "task_success_rate" in run["metrics"]
        assert "tool_selection_f1" in run["metrics"]


if __name__ == "__main__":
    tests = [
        test_task_success_metric,
        test_tool_selection_accuracy,
        test_tool_execution_success,
        test_efficiency_metric,
        test_evaluator_harness,
        test_mlflow_tracking_logging,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✓ {t.__name__} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__} FAILED: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
    if passed != len(tests):
        sys.exit(1)
