"""Evaluation harness executing benchmark tests across 4 agent configurations."""

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


# Dynamically load the agent architectures
def _load_components():
    base = Path(__file__).resolve().parent.parent

    # Lab 1
    lab1_dir = base / "01-tool-calling"
    if str(lab1_dir) not in sys.path:
        sys.path.insert(0, str(lab1_dir))
    import importlib.util

    s1 = importlib.util.spec_from_file_location("agent_mod", lab1_dir / "react_agent.py")
    m1 = importlib.util.module_from_spec(s1)
    s1.loader.exec_module(m1)
    ReActAgent = m1.ReActAgent

    # Lab 3
    lab3_dir = base / "03-memory"
    if str(lab3_dir) not in sys.path:
        sys.path.insert(0, str(lab3_dir))
    s3 = importlib.util.spec_from_file_location("mem_mod", lab3_dir / "memory_agent.py")
    m3 = importlib.util.module_from_spec(s3)
    s3.loader.exec_module(m3)
    MemoryAugmentedAgent = m3.MemoryAugmentedAgent

    # Lab 4
    lab4_dir = base / "04-multi-agent"
    if str(lab4_dir) not in sys.path:
        sys.path.insert(0, str(lab4_dir))
    s4 = importlib.util.spec_from_file_location("sup_mod", lab4_dir / "supervisor.py")
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
        """Run all test cases against a single agent configuration."""
        records: List[Dict[str, Any]] = []

        for tc in self.test_cases:
            t0 = time.time()
            prompt = tc["prompt"]
            user_id = tc.get("user_id", "eval_user")
            session_id = tc.get("session_id", "eval_session")

            try:
                # Execute agent
                if hasattr(agent, "run") and "user_id" in agent.run.__code__.co_varnames:
                    output = agent.run(prompt, user_id=user_id, session_id=session_id)
                else:
                    output = agent.run(prompt)
                latency = time.time() - t0
                error_occurred = False
            except Exception as e:
                output = f"Execution error: {e}"
                latency = time.time() - t0
                error_occurred = True

            # Extract tools actually called
            actual_tools: List[str] = []
            steps = 1
            if hasattr(agent, "logger"):
                for tr in agent.logger.get_traces():
                    if tr.get("type") == "ACTION":
                        content = tr.get("content", "")
                        for t_name in ["calculate", "search_papers", "get_paper_details", "save_preference", "get_preferences", "save_research_note"]:
                            if t_name in content:
                                actual_tools.append(t_name)
                steps = max(1, len(agent.logger.get_traces()))
                agent.logger.clear()

            # Compute metrics
            success = compute_task_success(
                output,
                required_keywords=tc.get("required_keywords"),
                forbidden_keywords=tc.get("forbidden_keywords"),
            )
            tool_acc = compute_tool_selection_accuracy(
                expected_tools=tc.get("expected_tools", []),
                actual_tools=actual_tools,
            )

            record = {
                "config": config_name,
                "test_id": tc["id"],
                "category": tc["category"],
                "success": 1 if success and not error_occurred else 0,
                "precision": tool_acc["precision"],
                "recall": tool_acc["recall"],
                "f1": tool_acc["f1"],
                "steps": steps,
                "latency_s": round(latency, 3),
            }
            records.append(record)

        return records

    def run_all(self) -> Dict[str, Any]:
        """Execute evaluation across all 4 configurations and aggregate summary results."""
        all_records: List[Dict[str, Any]] = []

        for name, agent in self.configurations.items():
            records = self.evaluate_configuration(name, agent)
            all_records.extend(records)

        # Aggregate metrics per configuration
        summary: List[Dict[str, Any]] = []
        for name in self.configurations.keys():
            cfg_records = [r for r in all_records if r["config"] == name]
            n = len(cfg_records) or 1
            success_rate = sum(r["success"] for r in cfg_records) / n
            avg_f1 = sum(r["f1"] for r in cfg_records) / n
            avg_steps = sum(r["steps"] for r in cfg_records) / n
            avg_latency = sum(r["latency_s"] for r in cfg_records) / n

            summary.append({
                "Configuration": name,
                "Success Rate": f"{round(success_rate * 100, 1)}%",
                "Tool F1 Score": round(avg_f1, 3),
                "Avg Steps": round(avg_steps, 1),
                "Avg Latency (s)": round(avg_latency, 3),
            })

        return {
            "summary": summary,
            "detailed_records": all_records,
        }

    def export_results(self, results: Dict[str, Any], output_prefix: str = "evaluation_results") -> None:
        """Export evaluation results to CSV and JSON."""
        json_path = f"{output_prefix}.json"
        csv_path = f"{output_prefix}.csv"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        records = results["detailed_records"]
        if records:
            keys = list(records[0].keys())
            lines = [",".join(keys)]
            for r in records:
                lines.append(",".join(str(r[k]) for k in keys))
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
