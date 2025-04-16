# Code generated by `py-sdk-gen`. DO NOT EDIT.
from datetime import datetime
import typing
import pydantic


class MembershipUserClassic(pydantic.BaseModel):
    """
            Classic identifiers of the user.
    Deprecated: this operation is deprecated
    """

    user_id: int
    """
	Format: int32
	"""


class MembershipUser(pydantic.BaseModel):
    """
    Information about the user associated with the membership.
    """

    email: str
    """
	End-User's preferred e-mail address. Its value MUST conform to the RFC 5322 [RFC5322] addr-spec syntax. TheRP MUST NOT rely upon this value being unique, for unique identification use ID instead.
	"""

    id: str
    """
	Identifier for the End-User (also called Subject).
	"""

    mfa_on_login_enabled: bool
    """
	True if the user has enabled MFA on login.
	"""

    service_account_user: bool
    """
	True if the user is a service account.
	"""

    virtual_user: bool
    """
	True if the user is a virtual user (operator).
	"""

    classic: typing.Optional[MembershipUserClassic] = None
    """
	Classic identifiers of the user.
	Deprecated: this operation is deprecated
	"""

    disabled_at: typing.Optional[datetime] = None
    """
	Time when the user has been disabled. Applies only to virtual users (`virtual_user: true`).
	"""

    nickname: typing.Optional[str] = None
    """
	User's preferred name. Used for display purposes only.
	"""

    picture: typing.Optional[str] = None
    """
	URL of the End-User's profile picture. This URL refers to an image file (for example, a PNG, JPEG, or GIFimage file), rather than to a Web page containing an image.
	Format: uri
	"""


class Invite(pydantic.BaseModel):
    """
    Pending invitation for membership.
    """

    email: str
    """
	Email address of the invited user.
	Format: email
	"""

    expires_at: datetime


MembershipStatus = typing.Literal["accepted", "disabled", "expired", "pending", "unknown"]

Metadata = dict[typing.Any, typing.Any]
"""
Set of user-defined key-value pairs attached to the object. Partial updates are not supported. When updating, alwayssubmit whole metadata.
"""

Attributes = dict[typing.Any, typing.Any]
"""
Object attributes that modifiable only by SumUp applications.
"""


class Member(pydantic.BaseModel):
    """
    A member is user within specific resource identified by resource id, resource type, and associated roles.
    """

    created_at: datetime
    """
	The timestamp of when the member was created.
	"""

    id: str
    """
	ID of the member.
	"""

    permissions: list[str]
    """
	User's permissions.
	"""

    roles: list[str]
    """
	User's roles.
	"""

    status: MembershipStatus
    """
	The status of the membership.
	"""

    updated_at: datetime
    """
	The timestamp of when the member was last updated.
	"""

    attributes: typing.Optional[Attributes] = None
    """
	Object attributes that modifiable only by SumUp applications.
	"""

    invite: typing.Optional[Invite] = None
    """
	Pending invitation for membership.
	"""

    metadata: typing.Optional[Metadata] = None
    """
	Set of user-defined key-value pairs attached to the object. Partial updates are not supported. When updating, alwayssubmit whole metadata.
	"""

    user: typing.Optional[MembershipUser] = None
    """
	Information about the user associated with the membership.
	"""
