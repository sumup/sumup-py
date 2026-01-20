import httpx
import platform
import sys
from functools import lru_cache

from ._api_version import __api_version__
from ._version import __version__

HeaderTypes = dict[str, str]


class BaseResource:
    @staticmethod
    def version():
        return f"v{__version__}"


def runtime_headers() -> dict[str, str]:
    return dict(_runtime_headers())


@lru_cache(maxsize=1)
def _runtime_headers() -> tuple[tuple[str, str], ...]:
    arch_raw = platform.machine()
    arch = arch_raw.lower() if arch_raw else ""
    arch_map = {
        "x86_64": "x86_64",
        "x64": "x86_64",
        "amd64": "x86_64",
        "x86": "x86",
        "i386": "x86",
        "i686": "x86",
        "ia32": "x86",
        "x32": "x86",
        "aarch64": "arm64",
        "arm64": "arm64",
        "arm": "arm",
    }
    arch = arch_map.get(arch, "unknown")

    os_name = sys.platform
    os_map = {
        "win32": "windows",
        "linux": "linux",
        "darwin": "darwin",
    }
    os_name = os_map.get(os_name, os_name)

    return (
        ("X-Sumup-Api-Version", __api_version__),
        ("X-Sumup-Lang", "python"),
        ("X-Sumup-Package-Version", __version__),
        ("X-Sumup-Os", os_name),
        ("X-Sumup-Arch", arch),
        ("X-Sumup-Runtime", "python"),
        ("X-Sumup-Runtime-Version", platform.python_version()),
    )


class Resource(BaseResource):
    _client: httpx.Client

    def __init__(self, client: httpx.Client) -> None:
        self._client = client


class AsyncResource(BaseResource):
    _client: httpx.AsyncClient

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
