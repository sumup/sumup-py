# Code generated by `py-sdk-gen`. DO NOT EDIT.
from .._service import Resource, AsyncResource, HeaderTypes
from .types import (
    Link,
    TransactionFull,
    TransactionHistory,
)
from datetime import datetime
import typing
import pydantic
import typing_extensions


class RefundTransactionBody(pydantic.BaseModel):
    """
    Optional amount for partial refunds of transactions.
    """

    amount: typing.Optional[float] = None
    """
	Amount to be refunded. Eligible amount can't exceed the amount of the transaction and varies based on countryand currency. If you do not specify a value, the system performs a full refund of the transaction.
	"""


class GetTransactionV21Params(pydantic.BaseModel):
    """
    GetTransactionV21Params: query parameters for GetTransactionV2.1
    """

    client_transaction_id: typing.Optional[str] = None

    foreign_transaction_id: typing.Optional[str] = None

    id: typing.Optional[str] = None

    internal_id: typing.Optional[str] = None

    transaction_code: typing.Optional[str] = None


class GetTransactionParams(pydantic.BaseModel):
    """
    GetTransactionParams: query parameters for GetTransaction
    """

    id: typing.Optional[str] = None

    internal_id: typing.Optional[str] = None

    transaction_code: typing.Optional[str] = None


class ListTransactionsV21Params(pydantic.BaseModel):
    """
    ListTransactionsV21Params: query parameters for ListTransactionsV2.1
    """

    changes_since: typing.Optional[datetime] = None

    limit: typing.Optional[int] = None

    newest_ref: typing.Optional[str] = None

    newest_time: typing.Optional[datetime] = None

    oldest_ref: typing.Optional[str] = None

    oldest_time: typing.Optional[datetime] = None

    order: typing.Optional[str] = None

    payment_types: typing.Optional[list[str]] = None

    statuses: typing.Optional[list[str]] = None

    transaction_code: typing.Optional[str] = None

    types: typing.Optional[list[str]] = None

    users: typing.Optional[list[str]] = None


class ListTransactionsParams(pydantic.BaseModel):
    """
    ListTransactionsParams: query parameters for ListTransactions
    """

    changes_since: typing.Optional[datetime] = None

    limit: typing.Optional[int] = None

    newest_ref: typing.Optional[str] = None

    newest_time: typing.Optional[datetime] = None

    oldest_ref: typing.Optional[str] = None

    oldest_time: typing.Optional[datetime] = None

    order: typing.Optional[str] = None

    payment_types: typing.Optional[list[str]] = None

    statuses: typing.Optional[list[str]] = None

    transaction_code: typing.Optional[str] = None

    types: typing.Optional[list[str]] = None

    users: typing.Optional[list[str]] = None


class ListTransactionsV21200Response(pydantic.BaseModel):
    """
    ListTransactionsV21200Response is a schema definition.
    """

    items: typing.Optional[list[TransactionHistory]] = None

    links: typing.Optional[list[Link]] = None


class ListTransactions200Response(pydantic.BaseModel):
    """
    ListTransactions200Response is a schema definition.
    """

    items: typing.Optional[list[TransactionHistory]] = None

    links: typing.Optional[list[Link]] = None


class TransactionsResource(Resource):
    def __init__(self, client):
        super().__init__(client)

    def refund(
        self, txn_id: str, body: RefundTransactionBody, headers: typing.Optional[HeaderTypes] = None
    ):
        """
        Refund a transaction

        Refunds an identified transaction either in full or partially.
        """
        self._client.post(
            f"/v0.1/me/refund/{txn_id}",
            json=body,
            headers=headers,
        )

    def get(
        self,
        merchant_code: str,
        params: typing.Optional[GetTransactionV21Params] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> TransactionFull:
        """
        Retrieve a transaction

        Retrieves the full details of an identified transaction. The transaction resource is identified by a query parameter and*one* of following parameters is required:

         *  `id`
         *  `internal_id`
         *  `transaction_code`
         *  `foreign_transaction_id`
         *  `client_transaction_id`
        """
        resp = self._client.get(
            f"/v2.1/merchants/{merchant_code}/transactions",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(TransactionFull).validate_python(resp.json())

    @typing_extensions.deprecated("This method is deprecated")
    def get_deprecated(
        self,
        params: typing.Optional[GetTransactionParams] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> TransactionFull:
        """
        Retrieve a transaction

        Retrieves the full details of an identified transaction. The transaction resource is identified by a query parameter and*one* of following parameters is required:

         *  `id`
         *  `internal_id`
         *  `transaction_code`
         *  `foreign_transaction_id`
         *  `client_transaction_id`
        """
        resp = self._client.get(
            "/v0.1/me/transactions",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(TransactionFull).validate_python(resp.json())

    def list(
        self,
        merchant_code: str,
        params: typing.Optional[ListTransactionsV21Params] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> ListTransactionsV21200Response:
        """
        List transactions

        Lists detailed history of all transactions associated with the merchant profile.
        """
        resp = self._client.get(
            f"/v2.1/merchants/{merchant_code}/transactions/history",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(ListTransactionsV21200Response).validate_python(resp.json())

    @typing_extensions.deprecated("This method is deprecated")
    def list_deprecated(
        self,
        params: typing.Optional[ListTransactionsParams] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> ListTransactions200Response:
        """
        List transactions

        Lists detailed history of all transactions associated with the merchant profile.
        """
        resp = self._client.get(
            "/v0.1/me/transactions/history",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(ListTransactions200Response).validate_python(resp.json())


class AsyncTransactionsResource(AsyncResource):
    def __init__(self, client):
        super().__init__(client)

    async def refund(
        self, txn_id: str, body: RefundTransactionBody, headers: typing.Optional[HeaderTypes] = None
    ):
        """
        Refund a transaction

        Refunds an identified transaction either in full or partially.
        """
        await self._client.post(
            f"/v0.1/me/refund/{txn_id}",
            json=body,
            headers=headers,
        )

    async def get(
        self,
        merchant_code: str,
        params: typing.Optional[GetTransactionV21Params] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> TransactionFull:
        """
        Retrieve a transaction

        Retrieves the full details of an identified transaction. The transaction resource is identified by a query parameter and*one* of following parameters is required:

         *  `id`
         *  `internal_id`
         *  `transaction_code`
         *  `foreign_transaction_id`
         *  `client_transaction_id`
        """
        resp = await self._client.get(
            f"/v2.1/merchants/{merchant_code}/transactions",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(TransactionFull).validate_python(resp.json())

    @typing_extensions.deprecated("This method is deprecated")
    async def get_deprecated(
        self,
        params: typing.Optional[GetTransactionParams] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> TransactionFull:
        """
        Retrieve a transaction

        Retrieves the full details of an identified transaction. The transaction resource is identified by a query parameter and*one* of following parameters is required:

         *  `id`
         *  `internal_id`
         *  `transaction_code`
         *  `foreign_transaction_id`
         *  `client_transaction_id`
        """
        resp = await self._client.get(
            "/v0.1/me/transactions",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(TransactionFull).validate_python(resp.json())

    async def list(
        self,
        merchant_code: str,
        params: typing.Optional[ListTransactionsV21Params] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> ListTransactionsV21200Response:
        """
        List transactions

        Lists detailed history of all transactions associated with the merchant profile.
        """
        resp = await self._client.get(
            f"/v2.1/merchants/{merchant_code}/transactions/history",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(ListTransactionsV21200Response).validate_python(resp.json())

    @typing_extensions.deprecated("This method is deprecated")
    async def list_deprecated(
        self,
        params: typing.Optional[ListTransactionsParams] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> ListTransactions200Response:
        """
        List transactions

        Lists detailed history of all transactions associated with the merchant profile.
        """
        resp = await self._client.get(
            "/v0.1/me/transactions/history",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(ListTransactions200Response).validate_python(resp.json())
