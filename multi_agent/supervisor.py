"""Supervisor agent entry point."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / "solutions" / "04-multi-agent" / "supervisor.py"
_spec = importlib.util.spec_from_file_location("sup_root_mod", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

SupervisorAgent = _mod.SupervisorAgent

__all__ = ["SupervisorAgent"]
