"""Writer agent: turns findings into a cited Markdown report."""

from __future__ import annotations

import logging

from app.agents.base import Agent, ResearchContext
from app.errors import LLMError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a meticulous research writer. Using ONLY the numbered findings provided, "
    "write a concise Markdown report with an '## Executive Summary' section followed by "
    "one '###' section per sub-question. Cite sources inline as [n]. Do not invent facts."
)


class WriterAgent(Agent):
    """Writes ``ctx.report_markdown`` with the LLM, or a structured template as fallback."""

    name = "writer"

    async def run(self, ctx: ResearchContext) -> str:
        """Produce the report body and append a references section."""
        body = ""
        if self._llm is not None and ctx.findings:
            try:
                body = await self._llm.complete(SYSTEM_PROMPT, self._build_prompt(ctx), 1500)
            except LLMError:
                logger.warning("writer_llm_failed_falling_back", exc_info=True)
        if not body:
            body = self._template_report(ctx)
        ctx.report_markdown = f"# {ctx.query}\n\n{body.strip()}\n\n{self._references(ctx)}"
        return f"Wrote report ({len(ctx.report_markdown)} chars)"

    @staticmethod
    def _build_prompt(ctx: ResearchContext) -> str:
        """Render the question, sub-questions and numbered findings for the LLM."""
        lines = [f"Question: {ctx.query}", "", "Findings:"]
        for f in ctx.findings:
            cites = "".join(f"[{i}]" for i in f.source_ids)
            lines.append(f"- ({f.sub_question}) {f.statement} {cites}")
        return "\n".join(lines)

    @staticmethod
    def _template_report(ctx: ResearchContext) -> str:
        """Build a deterministic report directly from the findings."""
        if not ctx.findings:
            return (
                "## Executive Summary\n\nNo sufficiently relevant information was found for "
                "this query. Try rephrasing it or using more specific terms."
            )
        top = sorted(ctx.findings, key=lambda f: f.score, reverse=True)[:3]
        summary = " ".join(f"{f.statement} {_cite(f.source_ids)}" for f in top)
        sections = ["## Executive Summary", "", summary, ""]
        for question in ctx.sub_questions:
            related = [f for f in ctx.findings if f.sub_question == question]
            if not related:
                continue
            sections.append(f"### {question}")
            sections.append("")
            sections.extend(f"- {f.statement} {_cite(f.source_ids)}" for f in related)
            sections.append("")
        return "\n".join(sections)

    @staticmethod
    def _references(ctx: ResearchContext) -> str:
        """Render the numbered reference list."""
        if not ctx.sources:
            return ""
        refs = "\n".join(f"{s.id}. [{s.title}]({s.url})" for s in ctx.sources)
        return f"## References\n\n{refs}\n"


def _cite(source_ids: list[int]) -> str:
    """Format citation markers like ``[1][3]``."""
    return "".join(f"[{i}]" for i in source_ids)
