"""Evaluation runner entry point."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / "solutions" / "05-evaluation" / "evaluator.py"
_spec = importlib.util.spec_from_file_location("eval_root_mod", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

AgentEvaluator = _mod.AgentEvaluator

if __name__ == "__main__":
    evaluator = AgentEvaluator()
    res = evaluator.run_all()
    evaluator.export_results(res)
    print("Evaluation completed. Results saved.")
