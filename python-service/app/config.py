"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable, failing loudly on bad values."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw!r}") from exc


def _env_float(name: str, default: float) -> float:
    """Read a float environment variable, failing loudly on bad values."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a number, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Immutable service settings.

    Attributes:
        anthropic_api_key: Optional key; when absent the agents use deterministic heuristics.
        anthropic_model: Claude model used by LLM-backed agents.
        search_base_url: Base URL of the MediaWiki API used as the search backend.
        http_timeout_seconds: Timeout applied to all outbound HTTP calls.
        max_sources_per_question: Upper bound on documents fetched per sub-question.
        log_level: Root log level.
    """

    anthropic_api_key: str | None
    anthropic_model: str
    search_base_url: str
    http_timeout_seconds: float
    max_sources_per_question: int
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from the current process environment."""
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5"),
            search_base_url=os.getenv("SEARCH_BASE_URL", "https://en.wikipedia.org/w/api.php"),
            http_timeout_seconds=_env_float("HTTP_TIMEOUT_SECONDS", 15.0),
            max_sources_per_question=_env_int("MAX_SOURCES_PER_QUESTION", 3),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
