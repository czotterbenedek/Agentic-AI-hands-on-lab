"""Evaluation harness executing benchmark tests across 4 agent configurations with MLflow experiment tracking."""

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

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False
    mlflow = None

from shared.agent import BaseAgent, Message
from shared.config import get_settings
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

    s4_orch = importlib.util.spec_from_file_location("orch_mod", lab4_dir / "orchestrator.py")
    m4_orch = importlib.util.module_from_spec(s4_orch)
    s4_orch.loader.exec_module(m4_orch)
    MultiAgentOrchestrator = m4_orch.MultiAgentOrchestrator

    return ReActAgent, MemoryAugmentedAgent, SupervisorAgent, MultiAgentOrchestrator


ReActAgent, MemoryAugmentedAgent, SupervisorAgent, MultiAgentOrchestrator = _load_components()


class BasicLLMAgent(BaseAgent):
    """Configuration 1: Direct model completion with no tool calling capabilities."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.client = llm_client or get_llm_client()

    def run(self, user_query: str, **kwargs: Any) -> str:
        res = self.client.complete(
            messages=[Message(role="user", content=user_query)],
            tools=None,
        )
        return res.content or ""


class LocalMLflowTracker:
    """Fallback local MLflow tracker storing parameters and metrics when MLflow is not installed."""

    def __init__(self, tracking_uri: str = "./mlruns", experiment_name: str = "agent_eval"):
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.runs: List[Dict[str, Any]] = []

    def log_run(self, run_name: str, params: Dict[str, Any], metrics: Dict[str, Any]) -> None:
        run_record = {
            "experiment": self.experiment_name,
            "run_name": run_name,
            "timestamp": time.time(),
            "params": params,
            "metrics": metrics,
        }
        self.runs.append(run_record)
        os.makedirs(self.tracking_uri, exist_ok=True)
        out_file = os.path.join(self.tracking_uri, f"{run_name.replace(' ', '_').replace('.', '')}.json")
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(run_record, f, indent=2)
        except Exception:
            pass


class AgentEvaluator:
    """Benchmark runner evaluating the four agent configurations with MLflow tracking."""

    def __init__(
        self,
        test_cases_path: Optional[str] = None,
        llm_client: Optional[BaseLLMClient] = None,
        experiment_name: Optional[str] = None,
    ):
        settings = get_settings()
        self.client = llm_client or get_llm_client()
        self.test_cases_path = test_cases_path or str(
            Path(__file__).resolve().parent / "test_cases.json"
        )
        self.test_cases = self._load_test_cases()
        self.experiment_name = experiment_name or settings.mlflow_experiment_name
        self.tracking_uri = settings.mlflow_tracking_uri

        # MLflow setup
        if HAS_MLFLOW:
            try:
                mlflow.set_tracking_uri(self.tracking_uri)
                mlflow.set_experiment(self.experiment_name)
            except Exception:
                pass
        self.local_tracker = LocalMLflowTracker(self.tracking_uri, self.experiment_name)

        # 4 Standard Configurations to compare
        self.configurations: Dict[str, BaseAgent] = {
            "1. Basic LLM (No tools)": BasicLLMAgent(llm_client=self.client),
            "2. Single ReAct Agent": ReActAgent(llm_client=self.client, verbose=False),
            "3. Agent with Memory": MemoryAugmentedAgent(llm_client=self.client, verbose=False),
            "4. Multi-Agent (LangGraph)": MultiAgentOrchestrator(
                supervisor=SupervisorAgent(llm_client=self.client, verbose=False),
                verbose=False,
            ),
        }

    def _load_test_cases(self) -> List[Dict[str, Any]]:
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
                        for t_name in [
                            "calculate",
                            "search_papers",
                            "get_paper_details",
                            "save_preference",
                            "get_preferences",
                            "save_research_note",
                        ]:
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

            # Tool execution success rate from observation traces
            observations = []
            if hasattr(agent, "logger"):
                for tr in agent.logger.get_traces():
                    if tr.get("type") == "OBSERVATION":
                        observations.append(tr.get("content", ""))
            tool_exec_success = compute_tool_execution_success(observations)

            # Efficiency metrics
            eff = compute_efficiency(step_count=steps, latency_seconds=latency)

            record = {
                "config": config_name,
                "test_id": tc["id"],
                "category": tc["category"],
                "success": 1 if success and not error_occurred else 0,
                "precision": tool_acc["precision"],
                "recall": tool_acc["recall"],
                "f1": tool_acc["f1"],
                "tool_execution_success": tool_exec_success,
                "steps": steps,
                "latency_s": round(latency, 3),
                "token_estimate": eff["token_estimate"],
            }
            records.append(record)

        return records

    def run_all(self) -> Dict[str, Any]:
        """Execute evaluation across all 4 configurations and track results in MLflow."""
        all_records: List[Dict[str, Any]] = []
        settings = get_settings()

        for name, agent in self.configurations.items():
            records = self.evaluate_configuration(name, agent)
            all_records.extend(records)

            # Compute summary metrics for this configuration
            n = len(records) or 1
            success_rate = sum(r["success"] for r in records) / n
            avg_f1 = sum(r["f1"] for r in records) / n
            avg_steps = sum(r["steps"] for r in records) / n
            avg_latency = sum(r["latency_s"] for r in records) / n

            params = {
                "config_name": name,
                "agent_type": agent.__class__.__name__,
                "test_case_count": len(self.test_cases),
                "llm_provider": settings.llm_provider,
                "llm_model": settings.llm_model,
            }
            metrics = {
                "task_success_rate": round(success_rate, 4),
                "tool_selection_f1": round(avg_f1, 4),
                "avg_steps": round(avg_steps, 2),
                "avg_latency_seconds": round(avg_latency, 4),
            }

            # MLflow logging
            if HAS_MLFLOW:
                try:
                    with mlflow.start_run(run_name=name):
                        mlflow.log_params(params)
                        mlflow.log_metrics(metrics)
                except Exception:
                    pass
            self.local_tracker.log_run(name, params, metrics)

        # Aggregate summary table
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

    def export_results(self, results: Dict[str, Any], output_prefix: str = "evaluation_benchmark") -> None:
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
