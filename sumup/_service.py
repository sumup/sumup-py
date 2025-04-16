import httpx

HeaderTypes = dict[str, str]


class BaseResource:
    @staticmethod
    def version():
        return "0.0.1"  # x-release-please-version


class Resource(BaseResource):
    _client: httpx.Client

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class AsyncResource(BaseResource):
    _client: httpx.AsyncClient

    def __init__(self, client: httpx.Client) -> None:
        self._client = client
