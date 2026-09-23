"""Analyst agent: extracts the most relevant, cited findings from the sources."""

from __future__ import annotations

from app.agents.base import Agent, ResearchContext
from app.models import Finding
from app.text import keywords, relevance, split_sentences

MIN_SCORE = 0.2


class AnalystAgent(Agent):
    """Scores every source sentence against each sub-question and keeps the best ones.

    This step is intentionally deterministic: it grounds every finding in a specific
    source sentence, which keeps the writer's output traceable to citations.
    """

    name = "analyst"

    def __init__(self, findings_per_question: int = 3) -> None:
        """Create an analyst that keeps up to ``findings_per_question`` findings each."""
        super().__init__(llm=None)
        self._per_question = findings_per_question

    async def run(self, ctx: ResearchContext) -> str:
        """Populate ``ctx.findings`` ordered by sub-question then score."""
        global_terms = keywords(ctx.query)
        used: set[str] = set()
        findings: list[Finding] = []
        for question in ctx.sub_questions:
            terms = _dedupe_terms(keywords(question) + global_terms)
            candidates: list[Finding] = []
            for source in ctx.sources:
                for sentence in split_sentences(source.content):
                    score = relevance(sentence, terms)
                    if score >= MIN_SCORE and sentence not in used:
                        candidates.append(
                            Finding(
                                sub_question=question,
                                statement=sentence,
                                source_ids=[source.id],
                                score=round(score, 3),
                            )
                        )
            candidates.sort(key=lambda f: f.score, reverse=True)
            for finding in candidates:
                if len([f for f in findings if f.sub_question == question]) >= self._per_question:
                    break
                if finding.statement not in used:
                    used.add(finding.statement)
                    findings.append(finding)
        ctx.findings = findings
        return f"Extracted {len(findings)} findings"


def _dedupe_terms(terms: list[str]) -> list[str]:
    """Remove duplicate terms preserving order."""
    return list(dict.fromkeys(terms))
