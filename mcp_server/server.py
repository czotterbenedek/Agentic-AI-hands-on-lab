"""MCP Server entry point for University Research Assistant."""

import importlib.util
from pathlib import Path
import sys

_server_path = Path(__file__).resolve().parent.parent / "solutions" / "02-mcp" / "server.py"
_dataset_path = Path(__file__).resolve().parent.parent / "solutions" / "02-mcp" / "dataset.py"

_spec_d = importlib.util.spec_from_file_location("dataset_mod", _dataset_path)
_mod_d = importlib.util.module_from_spec(_spec_d)
_spec_d.loader.exec_module(_mod_d)

_spec_s = importlib.util.spec_from_file_location("server_mod", _server_path)
_mod_s = importlib.util.module_from_spec(_spec_s)
_spec_s.loader.exec_module(_mod_s)

ResearchMCPServer = _mod_s.ResearchMCPServer

if __name__ == "__main__":
    server = ResearchMCPServer()
    server.run_stdio()
