import httpx
from ._version import __version__

HeaderTypes = dict[str, str]


class BaseResource:
    @staticmethod
    def version():
        return f"v{__version__}"


class Resource(BaseResource):
    _client: httpx.Client

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class AsyncResource(BaseResource):
    _client: httpx.AsyncClient

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
