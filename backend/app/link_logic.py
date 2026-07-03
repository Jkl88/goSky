"""Логика активности ссылок, IP и определение устройства."""

from __future__ import annotations

import re
from datetime import datetime

from fastapi import Request

from .models import ShortLink


_BOT_RE = re.compile(r"bot|crawler|spider|slurp|facebookexternalhit", re.I)
_MOBILE_RE = re.compile(r"mobile|android|iphone|ipod|windows phone", re.I)
_TABLET_RE = re.compile(r"ipad|tablet|kindle", re.I)


def request_ip_address(request: Request) -> str | None:
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",", 1)[0].strip()
    if forwarded:
        return forwarded[:64]
    if request.client and request.client.host:
        return request.client.host[:64]
    return None


def parse_device_type(user_agent: str | None) -> str:
    ua = (user_agent or "").strip()
    if not ua:
        return "unknown"
    if _BOT_RE.search(ua):
        return "bot"
    if _TABLET_RE.search(ua):
        return "tablet"
    if _MOBILE_RE.search(ua):
        return "mobile"
    return "desktop"


def device_label(device_type: str) -> str:
    return {
        "mobile": "Мобильное",
        "tablet": "Планшет",
        "desktop": "Компьютер",
        "bot": "Бот",
        "unknown": "Неизвестно",
    }.get(device_type, device_type)


InactiveKind = str  # "disabled" | "expired" | "max_clicks"


def is_link_active(link: ShortLink, now: datetime | None = None) -> bool:
    now = now or datetime.utcnow()
    if not link.is_enabled:
        return False
    if link.expires_at is not None and link.expires_at <= now:
        return False
    if link.max_clicks is not None and link.click_count >= link.max_clicks:
        return False
    return True


def inactive_kind(link: ShortLink, now: datetime | None = None) -> InactiveKind | None:
    if is_link_active(link, now):
        return None
    if not link.is_enabled:
        return "disabled"
    now = now or datetime.utcnow()
    if link.expires_at is not None and link.expires_at <= now:
        return "expired"
    if link.max_clicks is not None and link.click_count >= link.max_clicks:
        return "max_clicks"
    return "disabled"


def inactive_reason(link: ShortLink, now: datetime | None = None) -> str | None:
    kind = inactive_kind(link, now)
    if kind is None:
        return None
    return {
        "disabled": "Ссылка отключена владельцем.",
        "expired": "Срок действия ссылки истёк.",
        "max_clicks": "Достигнут лимит переходов.",
    }.get(kind, "Ссылка неактивна.")
