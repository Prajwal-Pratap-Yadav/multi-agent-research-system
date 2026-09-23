"""Planner agent: decomposes a research query into focused sub-questions."""

from __future__ import annotations

import logging
import re

from app.agents.base import Agent, ResearchContext
from app.errors import LLMError
from app.text import keywords

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a research planner. Break the user's question into distinct, searchable "
    "sub-questions. Respond with one sub-question per line and nothing else."
)

_TEMPLATES = (
    "What is {topic}?",
    "What are the key developments and history of {topic}?",
    "What are the main applications and impact of {topic}?",
    "What are the challenges and criticisms of {topic}?",
    "What is the future outlook for {topic}?",
)


class PlannerAgent(Agent):
    """Produces ``ctx.sub_questions`` using the LLM, or templates as a fallback."""

    name = "planner"

    async def run(self, ctx: ResearchContext) -> str:
        """Populate ``ctx.sub_questions`` (always including the original query first)."""
        planned: list[str] = []
        if self._llm is not None:
            try:
                planned = await self._plan_with_llm(ctx)
            except LLMError:
                logger.warning("planner_llm_failed_falling_back", exc_info=True)
        if not planned:
            planned = self._plan_heuristically(ctx)
        ctx.sub_questions = _dedupe([ctx.query, *planned])[: ctx.max_sub_questions]
        return f"Planned {len(ctx.sub_questions)} sub-questions"

    async def _plan_with_llm(self, ctx: ResearchContext) -> list[str]:
        """Ask the LLM for sub-questions and parse its line-oriented output."""
        assert self._llm is not None
        text = await self._llm.complete(
            SYSTEM_PROMPT,
            f"Question: {ctx.query}\nReturn at most {ctx.max_sub_questions} sub-questions.",
            max_tokens=300,
        )
        lines = (re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip() for line in text.splitlines())
        return [line for line in lines if len(line) > 5]

    @staticmethod
    def _plan_heuristically(ctx: ResearchContext) -> list[str]:
        """Expand the query's key terms into templated sub-questions."""
        topic = " ".join(keywords(ctx.query)[:6]) or ctx.query
        return [template.format(topic=topic) for template in _TEMPLATES]


def _dedupe(items: list[str]) -> list[str]:
    """Remove case-insensitive duplicates while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
