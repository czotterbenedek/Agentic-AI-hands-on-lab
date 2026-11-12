"""Unified test suite executing validation across all 5 solution modules."""

import os
import subprocess
import sys
from pathlib import Path


def run_solution_test(module_dir_name: str) -> None:
    test_path = Path(__file__).resolve().parent.parent / "solutions" / module_dir_name / "test_lab.py"
    assert test_path.exists(), f"Test file not found: {test_path}"

    res = subprocess.run(
        [sys.executable, str(test_path)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print(f"FAILED {module_dir_name}:\n{res.stdout}\n{res.stderr}")
    assert res.returncode == 0, f"Tests failed for {module_dir_name}"


def test_solution_01_tool_calling():
    run_solution_test("01-tool-calling")


def test_solution_02_mcp():
    run_solution_test("02-mcp")


def test_solution_03_memory():
    run_solution_test("03-memory")


def test_solution_04_multi_agent():
    run_solution_test("04-multi-agent")


def test_solution_05_evaluation():
    run_solution_test("05-evaluation")


if __name__ == "__main__":
    tests = [
        test_solution_01_tool_calling,
        test_solution_02_mcp,
        test_solution_03_memory,
        test_solution_04_multi_agent,
        test_solution_05_evaluation,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✓ {t.__name__} PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__} FAILED: {e}")
    print(f"\nAll {passed}/{len(tests)} solution suites passed successfully!")
    if passed != len(tests):
        sys.exit(1)
