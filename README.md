<div align="center">

# sumup-py

[![pypi](https://img.shields.io/pypi/v/sumup.svg)](https://pypi.python.org/pypi/sumup)
[![CI Status](https://github.com/sumup/sumup-py/workflows/CI/badge.svg)](https://github.com/sumup/sumup-py/actions/workflows/ci.yml)

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
