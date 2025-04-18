# Code generated by `py-sdk-gen`. DO NOT EDIT.
from .._service import Resource, AsyncResource, HeaderTypes
from .types import Operator
import typing
import pydantic
import typing_extensions


class CreateSubAccountBodyPermissions(pydantic.BaseModel):
    """
    CreateSubAccountBodyPermissions is a schema definition.
    """

    create_moto_payments: typing.Optional[bool] = None

    create_referral: typing.Optional[bool] = None

    full_transaction_history_view: typing.Optional[bool] = None

    refund_transactions: typing.Optional[bool] = None


class CreateSubAccountBody(pydantic.BaseModel):
    """
    CreateSubAccountBody is a schema definition.
    """

    password: str
    """
	Min length: 8
	"""

    username: str
    """
	Format: email
	"""

    nickname: typing.Optional[str] = None

    permissions: typing.Optional[CreateSubAccountBodyPermissions] = None


class UpdateSubAccountBodyPermissions(pydantic.BaseModel):
    """
    UpdateSubAccountBodyPermissions is a schema definition.
    """

    create_moto_payments: typing.Optional[bool] = None

    create_referral: typing.Optional[bool] = None

    full_transaction_history_view: typing.Optional[bool] = None

    refund_transactions: typing.Optional[bool] = None


class UpdateSubAccountBody(pydantic.BaseModel):
    """
    UpdateSubAccountBody is a schema definition.
    """

    disabled: typing.Optional[bool] = None

    nickname: typing.Optional[str] = None

    password: typing.Optional[str] = None
    """
	Min length: 8
	"""

    permissions: typing.Optional[UpdateSubAccountBodyPermissions] = None

    username: typing.Optional[str] = None
    """
	Format: email
	Max length: 256
	"""


class ListSubAccountsParams(pydantic.BaseModel):
    """
    ListSubAccountsParams: query parameters for ListSubAccounts
    """

    include_primary: typing.Optional[bool] = None

    query: typing.Optional[str] = None


ListSubAccounts200Response = list[Operator]
"""
ListSubAccounts200Response is a schema definition.
"""


class SubaccountsResource(Resource):
    def __init__(self, client):
        super().__init__(client)

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to list users in your merchant account please use [List members](https://developer.sumup.com/api/members/list) instead."
    )
    def list_sub_accounts(
        self,
        params: typing.Optional[ListSubAccountsParams] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> ListSubAccounts200Response:
        """
        List operators

        Returns list of operators for currently authorized user's merchant.
        """
        resp = self._client.get(
            "/v0.1/me/accounts",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(ListSubAccounts200Response).validate_python(resp.json())

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to create an user in your merchant account please use [Create member](https://developer.sumup.com/api/members/create) instead."
    )
    def create_sub_account(
        self, body: CreateSubAccountBody, headers: typing.Optional[HeaderTypes] = None
    ) -> Operator:
        """
        Create an operator

        Creates new operator for currently authorized users' merchant.
        """
        resp = self._client.post(
            "/v0.1/me/accounts",
            json=body,
            headers=headers,
        )
        return pydantic.TypeAdapter(Operator).validate_python(resp.json())

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to get an user that's a member of your merchant account please use [Get member](https://developer.sumup.com/api/members/get) instead."
    )
    def compat_get_operator(
        self, operator_id: int, headers: typing.Optional[HeaderTypes] = None
    ) -> Operator:
        """
        Retrieve an operator

        Returns specific operator.
        """
        resp = self._client.get(
            f"/v0.1/me/accounts/{operator_id}",
            headers=headers,
        )
        return pydantic.TypeAdapter(Operator).validate_python(resp.json())

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to update an user that's a member of your merchant account please use [Update member](https://developer.sumup.com/api/members/update) instead."
    )
    def update_sub_account(
        self,
        operator_id: int,
        body: UpdateSubAccountBody,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> Operator:
        """
        Update an operator

        Updates operator. If the operator was disabled and their password is updated they will be unblocked.
        """
        resp = self._client.put(
            f"/v0.1/me/accounts/{operator_id}",
            json=body,
            headers=headers,
        )
        return pydantic.TypeAdapter(Operator).validate_python(resp.json())

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to remove an user that's a member of your merchant account please use [Delete member](https://developer.sumup.com/api/members/delete) instead."
    )
    def deactivate_sub_account(
        self, operator_id: int, headers: typing.Optional[HeaderTypes] = None
    ) -> Operator:
        """
        Disable an operator
        """
        resp = self._client.delete(
            f"/v0.1/me/accounts/{operator_id}",
            headers=headers,
        )
        return pydantic.TypeAdapter(Operator).validate_python(resp.json())


class AsyncSubaccountsResource(AsyncResource):
    def __init__(self, client):
        super().__init__(client)

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to list users in your merchant account please use [List members](https://developer.sumup.com/api/members/list) instead."
    )
    async def list_sub_accounts(
        self,
        params: typing.Optional[ListSubAccountsParams] = None,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> ListSubAccounts200Response:
        """
        List operators

        Returns list of operators for currently authorized user's merchant.
        """
        resp = await self._client.get(
            "/v0.1/me/accounts",
            params=params.dict() if params else None,
            headers=headers,
        )
        return pydantic.TypeAdapter(ListSubAccounts200Response).validate_python(resp.json())

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to create an user in your merchant account please use [Create member](https://developer.sumup.com/api/members/create) instead."
    )
    async def create_sub_account(
        self, body: CreateSubAccountBody, headers: typing.Optional[HeaderTypes] = None
    ) -> Operator:
        """
        Create an operator

        Creates new operator for currently authorized users' merchant.
        """
        resp = await self._client.post(
            "/v0.1/me/accounts",
            json=body,
            headers=headers,
        )
        return pydantic.TypeAdapter(Operator).validate_python(resp.json())

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to get an user that's a member of your merchant account please use [Get member](https://developer.sumup.com/api/members/get) instead."
    )
    async def compat_get_operator(
        self, operator_id: int, headers: typing.Optional[HeaderTypes] = None
    ) -> Operator:
        """
        Retrieve an operator

        Returns specific operator.
        """
        resp = await self._client.get(
            f"/v0.1/me/accounts/{operator_id}",
            headers=headers,
        )
        return pydantic.TypeAdapter(Operator).validate_python(resp.json())

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to update an user that's a member of your merchant account please use [Update member](https://developer.sumup.com/api/members/update) instead."
    )
    async def update_sub_account(
        self,
        operator_id: int,
        body: UpdateSubAccountBody,
        headers: typing.Optional[HeaderTypes] = None,
    ) -> Operator:
        """
        Update an operator

        Updates operator. If the operator was disabled and their password is updated they will be unblocked.
        """
        resp = await self._client.put(
            f"/v0.1/me/accounts/{operator_id}",
            json=body,
            headers=headers,
        )
        return pydantic.TypeAdapter(Operator).validate_python(resp.json())

    @typing_extensions.deprecated(
        "Subaccounts API is deprecated, to remove an user that's a member of your merchant account please use [Delete member](https://developer.sumup.com/api/members/delete) instead."
    )
    async def deactivate_sub_account(
        self, operator_id: int, headers: typing.Optional[HeaderTypes] = None
    ) -> Operator:
        """
        Disable an operator
        """
        resp = await self._client.delete(
            f"/v0.1/me/accounts/{operator_id}",
            headers=headers,
        )
        return pydantic.TypeAdapter(Operator).validate_python(resp.json())
