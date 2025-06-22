<div align="center">

# sumup-py

[![pypi](https://img.shields.io/pypi/v/sumup.svg)](https://pypi.python.org/pypi/sumup)
[![Documentation][docs-badge]](https://developer.sumup.com)
[![CI Status](https://github.com/sumup/sumup-py/workflows/CI/badge.svg)](https://github.com/sumup/sumup-py/actions/workflows/ci.yml)
[![pypi download](https://img.shields.io/pypi/dm/sumup)](https://pypi.python.org/pypi/sumup)
[![License](https://img.shields.io/github/license/sumup/sumup-py)](./LICENSE)

</div>

_**IMPORTANT:** This SDK is under heavy development and subject to breaking changes._

The Python SDK for the SumUp [API](https://developer.sumup.com).

## Installation

Install the latest version of the SumUp SDK:

```sh
pip install sumup
# or
uv add sumup
```

## Usage

```python
from sumup import Sumup

client = Sumup(api_key="sup_sk_MvxmLOl0...")

merchant = client.merchant.get()
print(merchant)
```

## Version support policy

`sumup-py` maintains compatibility with Python versions that are no pass their End of life support, see [Status of Python versions](https://devguide.python.org/versions/).

[docs-badge]: https://img.shields.io/badge/SumUp-documentation-white.svg?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgY29sb3I9IndoaXRlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogICAgPHBhdGggZD0iTTIyLjI5IDBIMS43Qy43NyAwIDAgLjc3IDAgMS43MVYyMi4zYzAgLjkzLjc3IDEuNyAxLjcxIDEuN0gyMi4zYy45NCAwIDEuNzEtLjc3IDEuNzEtMS43MVYxLjdDMjQgLjc3IDIzLjIzIDAgMjIuMjkgMFptLTcuMjIgMTguMDdhNS42MiA1LjYyIDAgMCAxLTcuNjguMjQuMzYuMzYgMCAwIDEtLjAxLS40OWw3LjQ0LTcuNDRhLjM1LjM1IDAgMCAxIC40OSAwIDUuNiA1LjYgMCAwIDEtLjI0IDcuNjlabTEuNTUtMTEuOS03LjQ0IDcuNDVhLjM1LjM1IDAgMCAxLS41IDAgNS42MSA1LjYxIDAgMCAxIDcuOS03Ljk2bC4wMy4wM2MuMTMuMTMuMTQuMzUuMDEuNDlaIiBmaWxsPSJjdXJyZW50Q29sb3IiLz4KPC9zdmc+
