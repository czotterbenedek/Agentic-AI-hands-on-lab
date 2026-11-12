"""Evaluation metrics calculation for agent benchmarking (Starter Lab)."""

import re
from typing import Any, Dict, List, Optional, Set


def compute_task_success(
    response_text: str,
    required_keywords: Optional[List[str]] = None,
    forbidden_keywords: Optional[List[str]] = None,
) -> bool:
    """Determine deterministic task success based on expected output keywords.

    # ==============================================================================
    # TODO [Lab 5.1]: Deterministic Task Success Metric (~35 lines)
    # ------------------------------------------------------------------------------
    # 1. If `response_text` is empty, return False.
    # 2. Lowercase the response text for case-insensitive matching.
    # 3. For each keyword in `required_keywords`:
    #    If `kw.lower()` is not in `response_text.lower()`, return False.
    # 4. For each keyword in `forbidden_keywords`:
    #    If `fkw.lower()` appears in response text (using word boundary `\b` regex), return False.
    # 5. Return True if all checks pass.
    # ==============================================================================
    """
    raise NotImplementedError("TODO [Lab 5.1]: Implement compute_task_success")


def compute_tool_selection_accuracy(
    expected_tools: List[str],
    actual_tools: List[str],
) -> Dict[str, float]:
    """Calculate Precision, Recall, and F1 score for agent tool selection.

    # ==============================================================================
    # TODO [Lab 5.2]: Tool Selection Accuracy (Precision, Recall, F1) (~45 lines)
    # ------------------------------------------------------------------------------
    # Compute information retrieval metrics for tool calls:
    # 1. Convert `expected_tools` and `actual_tools` to sets.
    # 2. If both are empty: return precision=1.0, recall=1.0, f1=1.0.
    # 3. If `actual_set` is empty but expected was not: return precision=0.0, recall=0.0, f1=0.0.
    # 4. If `expected_set` is empty but actual was not: return precision=0.0, recall=1.0, f1=0.0.
    # 5. True Positives (TP) = len(expected_set & actual_set).
    # 6. Precision = TP / len(actual_set).
    # 7. Recall = TP / len(expected_set).
    # 8. F1 = 2 * (Precision * Recall) / (Precision + Recall) (or 0.0 if denominator is 0).
    # 9. Return dict with rounded floats (4 decimals).
    # ==============================================================================
    """
    raise NotImplementedError("TODO [Lab 5.2]: Implement compute_tool_selection_accuracy")


def compute_tool_execution_success(tool_results: List[str]) -> float:
    """Calculate the percentage of tool invocations that succeeded without error.

    # ==============================================================================
    # TODO [Lab 5.3a]: Tool Execution Success Rate (~20 lines)
    # ------------------------------------------------------------------------------
    # 1. If `tool_results` is empty, return 1.0.
    # 2. Count results containing "error", "exception", or "invalid".
    # 3. Success rate = (total - errors) / total.
    # 4. Return rounded to 4 decimals.
    # ==============================================================================
    """
    raise NotImplementedError("TODO [Lab 5.3a]: Implement compute_tool_execution_success")


def compute_efficiency(
    step_count: int,
    latency_seconds: float,
    token_estimate: Optional[int] = None,
) -> Dict[str, Any]:
    """Aggregate step efficiency, execution latency, and token consumption.

    # ==============================================================================
    # TODO [Lab 5.3b]: Efficiency & Resource Consumption Metric (~15 lines)
    # ------------------------------------------------------------------------------
    # Return dictionary with:
    # - "step_count": step_count
    # - "latency_seconds": round(latency_seconds, 3)
    # - "token_estimate": token_estimate if given, else step_count * 120
    # ==============================================================================
    """
    raise NotImplementedError("TODO [Lab 5.3b]: Implement compute_efficiency")
