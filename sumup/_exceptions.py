import typing


class SumupError(Exception):
    pass


class APIError(SumupError):
    message: str

    status: typing.Optional[int]
    body: typing.Optional[object]

    """The API response body.

    If the API responded with a valid JSON structure then this property will be the
    decoded result.

    If it isn't a valid JSON structure then this will be the raw response.

    If there was no response associated with this error then it will be `None`.
    """

    def __init__(
        self, message: str, *, status: typing.Optional[int], body: typing.Optional[object]
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.body = body
