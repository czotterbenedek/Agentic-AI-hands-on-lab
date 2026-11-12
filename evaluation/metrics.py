"""Deterministic evaluation metrics."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / "solutions" / "05-evaluation" / "metrics.py"
_spec = importlib.util.spec_from_file_location("metrics_root_mod", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

compute_task_success = _mod.compute_task_success
compute_tool_selection_accuracy = _mod.compute_tool_selection_accuracy
compute_tool_execution_success = _mod.compute_tool_execution_success
compute_efficiency = _mod.compute_efficiency

__all__ = [
    "compute_task_success",
    "compute_tool_selection_accuracy",
    "compute_tool_execution_success",
    "compute_efficiency",
]
