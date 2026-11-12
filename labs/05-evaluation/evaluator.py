"""Evaluation harness executing benchmark tests across 4 agent configurations (Starter Lab)."""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
except ImportError:
    pd = None

from shared.agent import BaseAgent, Message
from shared.llm_client import BaseLLMClient, get_llm_client

try:
    from .metrics import (
        compute_task_success,
        compute_tool_selection_accuracy,
        compute_tool_execution_success,
        compute_efficiency,
    )
except ImportError:
    from metrics import (
        compute_task_success,
        compute_tool_selection_accuracy,
        compute_tool_execution_success,
        compute_efficiency,
    )


def _load_components():
    current_dir = Path(__file__).resolve().parent
    base = current_dir.parent
    if not (base / "01-tool-calling" / "react_agent.py").exists():
        base = current_dir.parent.parent / "solutions"

    # Lab 1
    lab1_dir = base / "01-tool-calling"
    if str(lab1_dir) not in sys.path:
        sys.path.insert(0, str(lab1_dir))
    import importlib.util

    s1 = importlib.util.spec_from_file_location("agent_mod_e", lab1_dir / "react_agent.py")
    m1 = importlib.util.module_from_spec(s1)
    s1.loader.exec_module(m1)
    ReActAgent = m1.ReActAgent

    # Lab 3
    lab3_dir = base / "03-memory"
    if str(lab3_dir) not in sys.path:
        sys.path.insert(0, str(lab3_dir))
    s3 = importlib.util.spec_from_file_location("mem_mod_e", lab3_dir / "memory_agent.py")
    m3 = importlib.util.module_from_spec(s3)
    s3.loader.exec_module(m3)
    MemoryAugmentedAgent = m3.MemoryAugmentedAgent

    # Lab 4
    lab4_dir = base / "04-multi-agent"
    if str(lab4_dir) not in sys.path:
        sys.path.insert(0, str(lab4_dir))
    s4 = importlib.util.spec_from_file_location("sup_mod_e", lab4_dir / "supervisor.py")
    m4 = importlib.util.module_from_spec(s4)
    s4.loader.exec_module(m4)
    SupervisorAgent = m4.SupervisorAgent

    return ReActAgent, MemoryAugmentedAgent, SupervisorAgent


class BasicLLMWrapper(BaseAgent):
    """Configuration 1: Baseline LLM without any tools."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.client = llm_client or get_llm_client()

    def run(self, user_query: str, **kwargs: Any) -> str:
        resp = self.client.complete(
            messages=[Message(role="user", content=user_query)],
            tools=None,
        )
        return resp.content or ""


class AgentEvaluator:
    """Benchmark runner evaluating the 4 configurations specified in implementation plan."""

    def __init__(self, test_cases_path: Optional[str] = None):
        if test_cases_path is None:
            test_cases_path = os.path.join(os.path.dirname(__file__), "test_cases.json")
        self.test_cases_path = test_cases_path
        self.test_cases: List[Dict[str, Any]] = self._load_test_cases()
        ReActAgent, MemoryAugmentedAgent, SupervisorAgent = _load_components()

        # Initialize the 4 target configurations
        self.configurations: Dict[str, BaseAgent] = {
            "1. Basic LLM (No tools)": BasicLLMWrapper(),
            "2. Single ReAct Agent": ReActAgent(verbose=False),
            "3. Agent with Memory": MemoryAugmentedAgent(verbose=False),
            "4. Multi-Agent System": SupervisorAgent(verbose=False),
        }

    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load benchmark dataset from JSON."""
        with open(self.test_cases_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate_configuration(
        self, config_name: str, agent: BaseAgent
    ) -> List[Dict[str, Any]]:
        """Run all test cases against a single agent configuration.

        # ==============================================================================
        # TODO [Lab 5.4]: Test Case Runner and Execution Harness (~65 lines)
        # ------------------------------------------------------------------------------
        # For each test case in `self.test_cases`:
        # 1. Start timer `t0 = time.time()`.
        # 2. Invoke `agent.run(...)` with prompt, handling optional user_id/session_id.
        # 3. Calculate latency `time.time() - t0`. Catch any execution errors.
        # 4. Extract tools called from `agent.logger.get_traces()` (filter ACTION traces).
        # 5. Compute task success with `compute_task_success(...)`.
        # 6. Compute tool accuracy with `compute_tool_selection_accuracy(...)`.
        # 7. Append a structured evaluation record dict:
        #    {
        #      "config": config_name, "test_id": tc["id"], "category": tc["category"],
        #      "success": 1 or 0, "precision": ..., "recall": ..., "f1": ...,
        #      "steps": steps, "latency_s": ...
        #    }
        # 8. Return list of records.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 5.4]: Implement evaluate_configuration")

    def run_all(self) -> Dict[str, Any]:
        """Execute evaluation across all 4 configurations and aggregate summary results.

        # ==============================================================================
        # TODO [Lab 5.5]: Metric Aggregation & Comparison Summary (~55 lines)
        # ------------------------------------------------------------------------------
        # 1. Iterate over `self.configurations.items()`:
        #    Call `self.evaluate_configuration(name, agent)` and collect all detailed records.
        # 2. For each configuration, aggregate:
        #    - Success Rate: mean(success) * 100
        #    - Tool F1 Score: mean(f1)
        #    - Avg Steps: mean(steps)
        #    - Avg Latency: mean(latency_s)
        # 3. Build summary list of dicts.
        # 4. Return {"summary": summary, "detailed_records": all_records}.
        # ==============================================================================
        """
        raise NotImplementedError("TODO [Lab 5.5]: Implement run_all")

    def export_results(self, results: Dict[str, Any], output_prefix: str = "evaluation_results") -> None:
        """Export evaluation results to CSV and JSON."""
        json_path = f"{output_prefix}.json"
        csv_path = f"{output_prefix}.csv"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        records = results.get("detailed_records", [])
        if records:
            keys = list(records[0].keys())
            lines = [",".join(keys)]
            for r in records:
                lines.append(",".join(str(r[k]) for k in keys))
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
