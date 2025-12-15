from collections.abc import Callable

import httpx
import pytest

from sumup import Sumup


@pytest.fixture
def sdk_factory():
    created_clients: list[httpx.Client] = []

    def factory(handler: Callable[[httpx.Request], httpx.Response]) -> Sumup:
        transport = httpx.MockTransport(handler)
        sdk = Sumup(api_key="test", base_url="https://api.sumup.test")
        original_client = sdk._client
        sdk._client = httpx.Client(
            base_url=original_client.base_url,
            timeout=original_client.timeout,
            headers=original_client.headers,
            transport=transport,
        )
        original_client.close()
        created_clients.append(sdk._client)
        return sdk

    yield factory

    for client in created_clients:
        client.close()
