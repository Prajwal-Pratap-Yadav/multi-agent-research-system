import httpx
import pytest

from app.errors import LLMError, SearchError
from app.llm import AnthropicClient
from app.search import WikipediaSearchProvider


def client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_wikipedia_provider_parses_pages_in_rank_order() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["gsrsearch"] == "quantum"
        return httpx.Response(
            200,
            json={
                "query": {
                    "pages": {
                        "2": {"index": 2, "title": "B", "fullurl": "u2", "extract": "b text"},
                        "1": {"index": 1, "title": "A", "fullurl": "u1", "extract": "a text"},
                        "3": {"index": 3, "title": "Empty", "fullurl": "u3"},
                    }
                }
            },
        )

    async with client(handler) as http:
        docs = await WikipediaSearchProvider(http, "https://wiki/api").search("quantum", 3)
    assert [d.title for d in docs] == ["A", "B"]


async def test_wikipedia_provider_wraps_http_errors() -> None:
    async with client(lambda r: httpx.Response(503)) as http:
        with pytest.raises(SearchError):
            await WikipediaSearchProvider(http, "https://wiki/api").search("q", 1)


async def test_wikipedia_provider_handles_no_results() -> None:
    async with client(lambda r: httpx.Response(200, json={"batchcomplete": ""})) as http:
        assert await WikipediaSearchProvider(http, "https://wiki/api").search("zzz", 1) == []


async def test_anthropic_client_returns_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "k"
        return httpx.Response(200, json={"content": [{"type": "text", "text": " hi "}]})

    async with client(handler) as http:
        assert await AnthropicClient(http, "k", "m").complete("s", "p") == "hi"


@pytest.mark.parametrize(
    "response",
    [httpx.Response(500, text="err"), httpx.Response(200, json={"content": []})],
)
async def test_anthropic_client_raises_on_bad_response(response: httpx.Response) -> None:
    async with client(lambda r: response) as http:
        with pytest.raises(LLMError):
            await AnthropicClient(http, "k", "m").complete("s", "p")
