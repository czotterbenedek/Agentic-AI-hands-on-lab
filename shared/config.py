"""Configuration settings loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file() -> None:
    """Lightweight .env loader that does not strictly require python-dotenv."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


_load_env_file()


@dataclass
class Settings:
    """Global configuration settings for the Agentic AI Hands-on Lab."""
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock").lower()
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    memory_db_path: str = os.getenv("MEMORY_DB_PATH", "agent_memory.db")
    max_iterations: int = int(os.getenv("MAX_ITERATIONS", "5"))
    max_delegation_depth: int = int(os.getenv("MAX_DELEGATION_DEPTH", "4"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # LangGraph Multi-Agent Configuration (Module 4)
    langgraph_recursion_limit: int = int(os.getenv("LANGGRAPH_RECURSION_LIMIT", "10"))

    # MLflow Tracking Configuration (Module 5)
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
    mlflow_experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "academic_research_agent_evaluation")


def get_settings() -> Settings:
    """Return the global settings instance."""
    return Settings()
