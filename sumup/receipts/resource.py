# Code generated by `py-sdk-gen`. DO NOT EDIT.
from .._service import Resource, AsyncResource, HeaderTypes
from .types import (
    Receipt,
)
import typing
import pydantic


class GetReceiptParams(pydantic.BaseModel):
    """
    GetReceiptParams: query parameters for GetReceipt
    """

    mid: str

    tx_event_id: typing.Optional[int] = None


class ReceiptsResource(Resource):
    def __init__(self, client):
        super().__init__(client)

    def get(
        self,
        id: str,
        params: typing.Optional[GetReceiptParams] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> Receipt:
        """
        Retrieve receipt details

        Retrieves receipt specific data for a transaction.
        """
        resp = self._client.get(
            f"/v1.1/receipts/{id}",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(Receipt).validate_python(resp.json())


class AsyncReceiptsResource(AsyncResource):
    def __init__(self, client):
        super().__init__(client)

    async def get(
        self,
        id: str,
        params: typing.Optional[GetReceiptParams] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> Receipt:
        """
        Retrieve receipt details

        Retrieves receipt specific data for a transaction.
        """
        resp = await self._client.get(
            f"/v1.1/receipts/{id}",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(Receipt).validate_python(resp.json())
