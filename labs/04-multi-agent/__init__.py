"""Module 4: Multi-Agent Systems and Handoff (Starter Lab)."""

from .schemas import HandoffMessage, SharedContext, AgentRole
from .specialists import ResearchSpecialist, AnalysisSpecialist
from .supervisor import SupervisorAgent
from .orchestrator import MultiAgentOrchestrator

__all__ = [
    "HandoffMessage",
    "SharedContext",
    "AgentRole",
    "ResearchSpecialist",
    "AnalysisSpecialist",
    "SupervisorAgent",
    "MultiAgentOrchestrator",
]
