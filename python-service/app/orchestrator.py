"""Orchestrator that runs the agents in sequence and records an execution trace."""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from app.agents import Agent, ResearchContext
from app.models import AgentTrace, ResearchReport, ResearchRequest

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Coordinates planner -> researcher -> analyst -> writer over a shared context."""

    def __init__(self, agents: Sequence[Agent], llm_enabled: bool) -> None:
        """Create an orchestrator for an ordered list of agents."""
        if not agents:
            raise ValueError("At least one agent is required")
        self._agents = list(agents)
        self._llm_enabled = llm_enabled

    async def run(self, request: ResearchRequest) -> ResearchReport:
        """Execute every agent and assemble the final report.

        Raises:
            ResearchError: propagated from any agent that cannot recover.
        """
        ctx = ResearchContext(query=request.query, max_sub_questions=request.max_sub_questions)
        trace: list[AgentTrace] = []
        for agent in self._agents:
            started = time.perf_counter()
            summary = await agent.run(ctx)
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            trace.append(AgentTrace(agent=agent.name, duration_ms=elapsed, summary=summary))
            logger.info(
                "agent_completed",
                extra={"agent": agent.name, "duration_ms": elapsed, "summary": summary},
            )
        return ResearchReport(
            query=ctx.query,
            sub_questions=ctx.sub_questions,
            findings=ctx.findings,
            sources=ctx.sources,
            report_markdown=ctx.report_markdown,
            llm_enabled=self._llm_enabled,
            trace=trace,
        )
