import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import build_orchestrator, create_app
from tests.conftest import FakeSearch

SETTINGS = Settings(
    anthropic_api_key=None,
    anthropic_model="m",
    search_base_url="http://unused",
    http_timeout_seconds=1,
    max_sources_per_question=2,
    log_level="WARNING",
)


def make_client(search: FakeSearch) -> TestClient:
    orchestrator = build_orchestrator(SETTINGS, search, llm=None)
    return TestClient(create_app(SETTINGS, orchestrator))


def test_health() -> None:
    with make_client(FakeSearch()) as c:
        assert c.get("/health").json()["status"] == "ok"


def test_research_end_to_end_with_fakes() -> None:
    with make_client(FakeSearch()) as c:
        resp = c.post("/research", json={"query": "  artificial   intelligence  "})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "artificial intelligence"
    assert [t["agent"] for t in body["trace"]] == ["planner", "researcher", "analyst", "writer"]
    assert body["sources"] and body["findings"]
    assert body["llm_enabled"] is False
    assert "X-Request-ID" in resp.headers


@pytest.mark.parametrize(
    "payload", [{"query": "  "}, {"query": "ab"}, {"query": "valid", "max_sub_questions": 9}, {}]
)
def test_research_rejects_invalid_input(payload: dict) -> None:
    with make_client(FakeSearch()) as c:
        assert c.post("/research", json=payload).status_code == 422


def test_research_returns_502_when_search_is_down() -> None:
    with make_client(FakeSearch(fail=True)) as c:
        resp = c.post("/research", json={"query": "anything at all"})
    assert resp.status_code == 502
