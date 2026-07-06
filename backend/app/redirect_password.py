"""Общая логика пароля на редирект и просмотр /vq."""

from __future__ import annotations

import secrets

from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from .config import settings
from .models import ShortLink
from .password_page import redirect_password_cookie_name
from .security import hash_token

REDIRECT_UNLOCK_MAX_AGE = 7 * 24 * 3600


def redirect_unlock_token(slug: str, password_hash: str) -> str:
    return hash_token(f"{slug}:{password_hash}")


def is_redirect_unlocked(link: ShortLink, request: Request) -> bool:
    if not link.redirect_password_hash:
        return True
    token = request.cookies.get(redirect_password_cookie_name(link.slug))
    if not token:
        return False
    expected = redirect_unlock_token(link.slug, link.redirect_password_hash)
    return secrets.compare_digest(token, expected)


def set_redirect_unlock_cookie(response: Response | RedirectResponse, link: ShortLink) -> None:
    if not link.redirect_password_hash:
        return
    response.set_cookie(
        key=redirect_password_cookie_name(link.slug),
        value=redirect_unlock_token(link.slug, link.redirect_password_hash),
        max_age=REDIRECT_UNLOCK_MAX_AGE,
        path="/",
        samesite="lax",
        httponly=True,
        secure=settings.cookie_secure,
    )
