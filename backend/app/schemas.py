from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

from .target_url import normalize_target_url


def serialize_utc_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[
    datetime,
    PlainSerializer(serialize_utc_datetime, return_type=str, when_used="json"),
]
OptionalUtcDatetime = Annotated[
    datetime | None,
    PlainSerializer(serialize_utc_datetime, return_type=str | None, when_used="json"),
]


class OrmUtcJsonModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(OrmUtcJsonModel):
    id: int
    login: str
    email: str
    role: str
    blocked: bool
    created_at: UtcDatetime


class SessionOut(OrmUtcJsonModel):
    id: int
    expires_at: UtcDatetime
    refresh_expires_at: UtcDatetime
    created_at: UtcDatetime
    last_seen_at: OptionalUtcDatetime = None
    user_agent: str | None = None
    ip_address: str | None = None
    current: bool = False


class QrLoginCreateOut(OrmUtcJsonModel):
    id: int
    login_url: str
    expires_at: UtcDatetime
    ttl_seconds: int


class QrLoginStatusOut(BaseModel):
    status: Literal["pending", "missing", "expired"]


class QrLoginConsumeIn(BaseModel):
    token: str = Field(min_length=1)


class ShortLinkOut(OrmUtcJsonModel):
    id: int
    slug: str
    target_url: str
    title: str | None = None
    is_private: bool
    is_enabled: bool = True
    click_count: int
    expires_at: OptionalUtcDatetime = None
    max_clicks: int | None = None
    is_active: bool = True
    inactive_reason: str | None = None
    created_at: UtcDatetime
    updated_at: OptionalUtcDatetime = None
    short_url: str = ""
    view_url: str = ""


class ShortLinkCreateIn(BaseModel):
    target_url: str = Field(min_length=1, max_length=2048)
    title: str | None = Field(default=None, max_length=255)
    is_private: bool = False
    expires_at: datetime | None = None
    max_clicks: int | None = Field(default=None, ge=1, le=1_000_000)
    ttl_hours: int | None = Field(default=None, ge=1, le=8760)

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, value: str) -> str:
        return normalize_target_url(value)


class ShortLinkUpdateIn(BaseModel):
    target_url: str | None = Field(default=None, min_length=1, max_length=2048)
    title: str | None = Field(default=None, max_length=255)
    is_private: bool | None = None
    is_enabled: bool | None = None
    expires_at: datetime | None = None
    max_clicks: int | None = Field(default=None, ge=1, le=1_000_000)
    clear_expires_at: bool = False
    clear_max_clicks: bool = False
    ttl_hours: int | None = Field(default=None, ge=1, le=8760)

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_target_url(value)


class ShortLinkViewOut(BaseModel):
    slug: str
    target_url: str
    title: str | None = None
    is_private: bool
    is_enabled: bool = True
    click_count: int
    expires_at: OptionalUtcDatetime = None
    max_clicks: int | None = None
    is_active: bool = True
    inactive_reason: str | None = None
    short_url: str
    view_url: str
    is_owner: bool = False
    can_edit: bool = False


class LinkClickOut(OrmUtcJsonModel):
    id: int
    ip_address: str | None
    user_agent: str | None
    device_type: str
    device_label: str = ""
    clicked_at: UtcDatetime


class LinkStatsOut(BaseModel):
    slug: str
    click_count: int
    unique_ips: int
    is_active: bool
    inactive_reason: str | None = None
    expires_at: OptionalUtcDatetime = None
    max_clicks: int | None = None
    device_breakdown: dict[str, int]
    clicks: list[LinkClickOut]
