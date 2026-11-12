"""Unit and integration tests for Module 4: Multi-Agent Systems and Handoff."""

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

from schemas import HandoffMessage, SharedContext, AgentRole
from specialists import ResearchSpecialist, AnalysisSpecialist
from supervisor import SupervisorAgent
from orchestrator import MultiAgentOrchestrator


def test_specialist_research_execution():
    """Verify ResearchSpecialist queries literature and updates context."""
    specialist = ResearchSpecialist(verbose=False)
    ctx = SharedContext(raw_query="transformer")
    handoff = HandoffMessage(
        source_agent="supervisor",
        target_agent="researcher",
        task_description="Search for transformer papers",
        context_payload={"query": "transformer", "limit": 2},
    )
    res = specialist.execute_task(handoff, ctx)
    assert res["status"] == "success"
    assert len(ctx.retrieved_papers) > 0
    assert any("Attention" in p["title"] for p in ctx.retrieved_papers)


def test_specialist_analysis_execution():
    """Verify AnalysisSpecialist computes statistics and methodology matrix."""
    researcher = ResearchSpecialist(verbose=False)
    analyst = AnalysisSpecialist(verbose=False)
    ctx = SharedContext(raw_query="lora")

    r_handoff = HandoffMessage(
        source_agent="supervisor",
        target_agent="researcher",
        task_description="Search LoRA",
        context_payload={"query": "lora", "limit": 2},
    )
    researcher.execute_task(r_handoff, ctx)

    a_handoff = HandoffMessage(
        source_agent="supervisor",
        target_agent="analyst",
        task_description="Analyze papers",
        context_payload={"papers": ctx.retrieved_papers},
    )
    res = analyst.execute_task(a_handoff, ctx)

    assert "citation_statistics" in res
    assert "methodology_matrix" in res
    assert ctx.analysis_artifacts["citation_statistics"]["total_citations"] > 0


def test_supervisor_coordination_and_synthesis():
    """Verify supervisor coordinates both specialists and generates final report."""
    supervisor = SupervisorAgent(verbose=False)
    report = supervisor.run("Compare LoRA and BERT")
    assert "Academic Literature Review & Synthesis" in report
    assert "Quantitative & Comparative Analysis" in report


def test_max_delegation_depth_limit():
    """Verify that exceeding max_delegation_depth stops further delegation."""
    supervisor = SupervisorAgent(max_delegation_depth=1, verbose=False)
    ctx = SharedContext(raw_query="test")
    # Simulate prior handoff
    ctx.record_handoff(
        HandoffMessage(source_agent="a", target_agent="b", task_description="prior")
    )
    supervisor.plan_and_delegate("test", ctx)
    # Since depth limit was 1, no further handoffs should be performed
    assert len(ctx.delegation_history) == 1


def test_cycle_detection():
    """Verify orchestrator detects ping-pong cycles between agents."""
    orchestrator = MultiAgentOrchestrator(verbose=False)
    history = [
        HandoffMessage(source_agent="agent_a", target_agent="agent_b", task_description="1"),
        HandoffMessage(source_agent="agent_b", target_agent="agent_a", task_description="2"),
        HandoffMessage(source_agent="agent_a", target_agent="agent_b", task_description="3"),
        HandoffMessage(source_agent="agent_b", target_agent="agent_a", task_description="4"),
    ]
    assert orchestrator.detect_cycle(history) is True


if __name__ == "__main__":
    tests = [
        test_specialist_research_execution,
        test_specialist_analysis_execution,
        test_supervisor_coordination_and_synthesis,
        test_max_delegation_depth_limit,
        test_cycle_detection,
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
