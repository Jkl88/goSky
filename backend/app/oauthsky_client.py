"""HTTP-клиент OAuthSky (SSO)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException, status

from .config import settings


def _api_base_url() -> str:
    return settings.oauthsky_api_base_url


def oauthsky_portal_url() -> str:
    return settings.oauthsky_portal_url


def oauthsky_redirect_uri() -> str:
    return (settings.oauthsky_redirect_uri_resolved or "").strip()


def oauthsky_configured() -> bool:
    return bool(
        settings.oauthsky_enabled
        and settings.oauthsky_portal_url
        and settings.oauthsky_api_base_url
        and (settings.oauthsky_client_id or "").strip()
        and (settings.oauthsky_client_secret or "").strip()
        and oauthsky_redirect_uri()
    )


def exchange_authorization_code(code: str, redirect_uri: str) -> dict[str, Any]:
    url = urljoin(_api_base_url() + "/", "api/auth/token")
    payload = {
        "grant_type": "authorization_code",
        "code": code.strip(),
        "client_id": settings.oauthsky_client_id.strip(),
        "client_secret": settings.oauthsky_client_secret.strip(),
        "redirect_uri": redirect_uri.strip(),
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(url, json=payload)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OAuthSky недоступен: {exc}",
        ) from exc
    if r.status_code >= 400:
        detail = "Ошибка обмена кода OAuthSky."
        try:
            body = r.json()
            if isinstance(body, dict) and body.get("detail"):
                detail = str(body["detail"])
        except Exception:
            pass
        raise HTTPException(status_code=r.status_code, detail=detail)
    return r.json()
