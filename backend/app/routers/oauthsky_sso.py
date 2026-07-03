"""Вход через OAuthSky (единый IdP)."""

import secrets
import time
from urllib.parse import quote, urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import UserSession
from ..oauthsky_client import (
    exchange_authorization_code,
    oauthsky_configured,
    oauthsky_portal_url,
    oauthsky_redirect_uri,
)
from ..oauthsky_provision import provision_user_from_oauthsky
from ..routers.auth import issue_session_pair
from ..security import hash_token

router = APIRouter(prefix="/api/auth/oauthsky", tags=["auth-oauthsky"])

_STATE_COOKIE = "gosky_oauthsky_state"


def _state_create(return_path: str = "/") -> str:
    payload = {
        "n": secrets.token_hex(8),
        "exp": int(time.time()) + 600,
        "rt": (return_path or "/")[:512],
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _state_load(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный state.") from exc
    if int(payload.get("exp") or 0) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Истёк срок state.")
    return str(payload.get("rt") or "/")


@router.get("/start")
def oauthsky_start(
    return_to: str = Query(default="/"),
):
    if not oauthsky_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Вход через OAuthSky не настроен.",
        )
    state = _state_create(return_to)
    redirect_uri = oauthsky_redirect_uri()
    q = urlencode(
        {
            "client_id": settings.oauthsky_client_id.strip(),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
        }
    )
    authorize_url = f"{oauthsky_portal_url()}/authorize?{q}"
    out = RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)
    out.set_cookie(
        key=_STATE_COOKIE,
        value=state,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=600,
    )
    return out


@router.get("/callback")
def oauthsky_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not oauthsky_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OAuthSky не настроен.")
    front = settings.frontend_public_origin.rstrip("/")
    if error:
        return RedirectResponse(
            url=f"{front}/?oauthsky_error={quote(str(error))}",
            status_code=status.HTTP_302_FOUND,
        )
    if not code or not state:
        return RedirectResponse(url=f"{front}/?oauthsky_error=missing_code", status_code=status.HTTP_302_FOUND)

    cookie_state = request.cookies.get(_STATE_COOKIE)
    if not cookie_state or cookie_state != state:
        return RedirectResponse(url=f"{front}/?oauthsky_error=invalid_state", status_code=status.HTTP_302_FOUND)

    return_path = _state_load(state)
    data = exchange_authorization_code(code, oauthsky_redirect_uri())
    sky_user = data.get("user") or {}
    local_user = provision_user_from_oauthsky(db, sky_user)

    db.query(UserSession).filter(UserSession.user_id == local_user.id, UserSession.revoked.is_(False)).update(
        {"revoked": True}
    )
    db.commit()

    redirect = RedirectResponse(url=f"{front}{return_path}?oauthsky=1", status_code=status.HTTP_302_FOUND)
    issue_session_pair(local_user, db, redirect, request)
    redirect.delete_cookie(
        _STATE_COOKIE,
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
    )
    return redirect
