import asyncio

import httpx
import pytest

from sumup import AsyncSumup, Sumup


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_explicit_close(use_async):
    if use_async:

        async def run():
            client = AsyncSumup(api_key="test")
            await client.aclose()
            await client.aclose()
            assert client._client.is_closed

        asyncio.run(run())
    else:
        client = Sumup(api_key="test")
        client.close()
        client.close()
        assert client._client.is_closed


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("raise_error", [False, True], ids=["success", "exception"])
def test_context_manager_closes_transport(use_async, raise_error, monkeypatch):
    error = ValueError("processing failed")

    def handler(request):
        return httpx.Response(200, json={"items": []})

    # Inject a transport so requests and cleanup can be tested without network access.
    transport = httpx.MockTransport(handler)
    if use_async:
        http_client = httpx.AsyncClient(base_url="https://api.sumup.test", transport=transport)
        monkeypatch.setattr("sumup._client.httpx.AsyncClient", lambda **kwargs: http_client)

        async def run():
            client = AsyncSumup(api_key="test")
            try:
                async with client as entered:
                    assert entered is client
                    assert not http_client.is_closed
                    page = await client.transactions.list("merchant-123")
                    assert page.items == []
                    if raise_error:
                        raise error
            except ValueError as caught:
                assert raise_error
                assert caught is error
            else:
                assert not raise_error
            assert http_client.is_closed

        asyncio.run(run())
    else:
        http_client = httpx.Client(base_url="https://api.sumup.test", transport=transport)
        monkeypatch.setattr("sumup._client.httpx.Client", lambda **kwargs: http_client)
        client = Sumup(api_key="test")
        try:
            with client as entered:
                assert entered is client
                assert not http_client.is_closed
                page = client.transactions.list("merchant-123")
                assert page.items == []
                if raise_error:
                    raise error
        except ValueError as caught:
            assert raise_error
            assert caught is error
        else:
            assert not raise_error
        assert http_client.is_closed
