import pytest

from app.agents import AnalystAgent, PlannerAgent, ResearchContext, ResearcherAgent, WriterAgent
from app.errors import SearchError
from app.models import Finding, Source
from tests.conftest import AI_DOC, FakeLLM, FakeSearch


def ctx(**kwargs) -> ResearchContext:
    return ResearchContext(query="artificial intelligence impact", max_sub_questions=3, **kwargs)


async def test_planner_heuristic_includes_query_first() -> None:
    c = ctx()
    await PlannerAgent(None).run(c)
    assert c.sub_questions[0] == "artificial intelligence impact"
    assert len(c.sub_questions) == 3


async def test_planner_parses_llm_lines() -> None:
    c = ctx()
    llm = FakeLLM("1. How is AI used in healthcare?\n- What risks does AI pose?")
    await PlannerAgent(llm).run(c)
    assert c.sub_questions[1:] == ["How is AI used in healthcare?", "What risks does AI pose?"]


async def test_planner_falls_back_when_llm_fails() -> None:
    c = ctx()
    await PlannerAgent(FakeLLM(fail=True)).run(c)
    assert len(c.sub_questions) == 3


async def test_researcher_dedupes_sources_across_questions(fake_search: FakeSearch) -> None:
    c = ctx(sub_questions=["q one", "q two"])
    await ResearcherAgent(fake_search, 5).run(c)
    assert [s.id for s in c.sources] == [1, 2]
    assert len(fake_search.queries) == 2


async def test_researcher_tolerates_partial_failure() -> None:
    class Flaky(FakeSearch):
        async def search(self, query: str, limit: int):
            if query == "bad":
                raise SearchError("nope")
            return await super().search(query, limit)

    c = ctx(sub_questions=["bad", "good"])
    summary = await ResearcherAgent(Flaky(), 5).run(c)
    assert len(c.sources) == 2
    assert "1 failed" in summary


async def test_researcher_raises_when_all_searches_fail() -> None:
    with pytest.raises(SearchError):
        await ResearcherAgent(FakeSearch(fail=True), 3).run(ctx(sub_questions=["a", "b"]))


async def test_analyst_extracts_cited_findings() -> None:
    source = Source(id=1, title=AI_DOC.title, url=AI_DOC.url, content=AI_DOC.content)
    c = ctx(sub_questions=["artificial intelligence impact"], sources=[source])
    await AnalystAgent(findings_per_question=2).run(c)
    assert 1 <= len(c.findings) <= 2
    assert all(f.source_ids == [1] for f in c.findings)
    assert c.findings == sorted(c.findings, key=lambda f: f.score, reverse=True)


def _populated_ctx() -> ResearchContext:
    return ctx(
        sub_questions=["artificial intelligence impact"],
        sources=[Source(id=1, title="AI", url="https://x/ai", content="...")],
        findings=[
            Finding(
                sub_question="artificial intelligence impact",
                statement="AI changes work.",
                source_ids=[1],
                score=0.9,
            )
        ],
    )


async def test_writer_template_contains_citations_and_references() -> None:
    c = _populated_ctx()
    await WriterAgent(None).run(c)
    assert "AI changes work. [1]" in c.report_markdown
    assert "## References" in c.report_markdown
    assert "1. [AI](https://x/ai)" in c.report_markdown


async def test_writer_uses_llm_output_when_available() -> None:
    c = _populated_ctx()
    llm = FakeLLM("## Executive Summary\n\nLLM text [1]")
    await WriterAgent(llm).run(c)
    assert "LLM text [1]" in c.report_markdown
    assert "AI changes work." in llm.calls[0]


async def test_writer_handles_no_findings() -> None:
    c = ctx()
    await WriterAgent(None).run(c)
    assert "No sufficiently relevant information" in c.report_markdown
