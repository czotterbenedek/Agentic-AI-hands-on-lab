"""Evaluation metrics calculation for agent benchmarking."""

import re
from typing import Any, Dict, List, Optional, Set


def compute_task_success(
    response_text: str,
    required_keywords: Optional[List[str]] = None,
    forbidden_keywords: Optional[List[str]] = None,
) -> bool:
    """Determine deterministic task success based on expected output keywords."""
    if not response_text:
        return False

    text_lower = response_text.lower()

    # Check for presence of required keywords
    if required_keywords:
        for kw in required_keywords:
            if kw.lower() not in text_lower:
                return False

    # Check for absence of forbidden keywords (e.g. fatal errors or hallucinations)
    if forbidden_keywords:
        for fkw in forbidden_keywords:
            # Match whole-word or exact substring
            if re.search(rf"\b{re.escape(fkw.lower())}\b", text_lower):
                return False

    return True


def compute_tool_selection_accuracy(
    expected_tools: List[str],
    actual_tools: List[str],
) -> Dict[str, float]:
    """Calculate Precision, Recall, and F1 score for agent tool selection."""
    expected_set: Set[str] = set(expected_tools)
    actual_set: Set[str] = set(actual_tools)

    if not expected_set and not actual_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    if not actual_set:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    if not expected_set:
        # Penalize calling tools when none were required
        return {"precision": 0.0, "recall": 1.0, "f1": 0.0}

    true_positives = len(expected_set & actual_set)
    precision = true_positives / len(actual_set)
    recall = true_positives / len(expected_set)

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def compute_tool_execution_success(tool_results: List[str]) -> float:
    """Calculate the percentage of tool invocations that succeeded without error."""
    if not tool_results:
        return 1.0

    errors = 0
    for res in tool_results:
        res_lower = res.lower()
        if "error" in res_lower or "exception" in res_lower or "invalid" in res_lower:
            errors += 1

    success_rate = (len(tool_results) - errors) / len(tool_results)
    return round(success_rate, 4)


def compute_efficiency(
    step_count: int,
    latency_seconds: float,
    token_estimate: Optional[int] = None,
) -> Dict[str, Any]:
    """Aggregate step efficiency, execution latency, and token consumption."""
    return {
        "step_count": step_count,
        "latency_seconds": round(latency_seconds, 3),
        "token_estimate": token_estimate if token_estimate is not None else step_count * 120,
    }
