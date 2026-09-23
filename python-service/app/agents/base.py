"""Common agent abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.llm import LLMClient
from app.models import Finding, Source


@dataclass
class ResearchContext:
    """Shared blackboard passed between agents; each agent reads and enriches it."""

    query: str
    max_sub_questions: int
    sub_questions: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    report_markdown: str = ""


class Agent(ABC):
    """Base class for pipeline agents.

    Subclasses implement :meth:`run`, mutate the context and return a one-line summary
    that is recorded in the execution trace.
    """

    name: str = "agent"

    def __init__(self, llm: LLMClient | None = None) -> None:
        """Create an agent, optionally backed by an LLM."""
        self._llm = llm

    @abstractmethod
    async def run(self, ctx: ResearchContext) -> str:
        """Execute the agent's step against ``ctx`` and return a trace summary."""
