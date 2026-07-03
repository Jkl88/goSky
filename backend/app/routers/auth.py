from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import QrLoginLink, User, UserSession
from ..oauthsky_client import oauthsky_configured
from ..schemas import (
    QrLoginConsumeIn,
    QrLoginCreateOut,
    QrLoginStatusOut,
    SessionOut,
    UserOut,
)
from ..security import generate_secure_token, hash_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

QR_LOGIN_TTL_SECONDS = 30


def _request_ip_address(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",", 1)[0].strip()
    if forwarded:
        return forwarded[:64]
    if request.client and request.client.host:
        return request.client.host[:64]
    return None


def issue_session_pair(user: User, db: Session, response: Response, request: Request | None = None) -> None:
    session_token = generate_secure_token(32)
    refresh_token = generate_secure_token(48)
    now = datetime.utcnow()
    session_row = UserSession(
        user_id=user.id,
        session_token_hash=hash_token(session_token),
        refresh_token_hash=hash_token(refresh_token),
        expires_at=now + timedelta(minutes=settings.session_expire_minutes),
        refresh_expires_at=now + timedelta(days=settings.refresh_expire_days),
        revoked=False,
        last_seen_at=now,
        user_agent=(request.headers.get("user-agent", "")[:512] if request else None),
        ip_address=_request_ip_address(request),
    )
    db.add(session_row)
    db.commit()

    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        max_age=settings.session_expire_minutes * 60,
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        max_age=settings.refresh_expire_days * 24 * 60 * 60,
    )


def clear_auth_cookies(response: Response) -> None:
    cookie_kwargs = {
        "path": "/",
        "samesite": "lax",
        "secure": settings.cookie_secure,
    }
    response.delete_cookie(settings.session_cookie_name, **cookie_kwargs)
    response.delete_cookie(settings.refresh_cookie_name, **cookie_kwargs)


@router.post("/logout")
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    db: Session = Depends(get_db),
):
    if session_token:
        session_row = db.query(UserSession).filter(
            UserSession.session_token_hash == hash_token(session_token),
            UserSession.revoked.is_(False),
        ).first()
        if session_row:
            session_row.revoked = True
            db.commit()
    clear_auth_cookies(response)
    return {"ok": True}


@router.post("/refresh", response_model=UserOut)
def refresh_session(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token отсутствует.")

    session_row = db.query(UserSession).filter(
        UserSession.refresh_token_hash == hash_token(refresh_token),
        UserSession.revoked.is_(False),
    ).first()
    now = datetime.utcnow()
    if not session_row or session_row.refresh_expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token недействителен или истек.")

    user = db.query(User).filter(User.id == session_row.user_id).first()
    if not user or user.blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь недоступен.")

    session_row.revoked = True
    db.commit()
    issue_session_pair(user, db, response, request)
    return user


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    current_session = getattr(getattr(request, "state", None), "user_session", None)
    current_session_id = int(current_session.id) if current_session is not None else 0
    rows = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == current_user.id,
            UserSession.revoked.is_(False),
            UserSession.refresh_expires_at > now,
        )
        .order_by(UserSession.last_seen_at.desc(), UserSession.created_at.desc())
        .all()
    )
    return [
        {
            "id": row.id,
            "expires_at": row.expires_at,
            "refresh_expires_at": row.refresh_expires_at,
            "created_at": row.created_at,
            "last_seen_at": row.last_seen_at,
            "user_agent": row.user_agent,
            "ip_address": row.ip_address,
            "current": row.id == current_session_id,
        }
        for row in rows
    ]


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: int,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(UserSession)
        .filter(UserSession.id == session_id, UserSession.user_id == current_user.id, UserSession.revoked.is_(False))
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена.")
    row.revoked = True
    db.add(row)
    db.commit()
    current_session = getattr(getattr(request, "state", None), "user_session", None)
    if current_session is not None and int(current_session.id) == int(session_id):
        clear_auth_cookies(response)
    return {"ok": True}


def _cleanup_expired_qr_login_links(db: Session, now: datetime) -> None:
    db.query(QrLoginLink).filter(QrLoginLink.expires_at <= now).delete(synchronize_session=False)


@router.post("/qr-login-links", response_model=QrLoginCreateOut)
def create_qr_login_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    _cleanup_expired_qr_login_links(db, now)
    db.query(QrLoginLink).filter(QrLoginLink.user_id == current_user.id).delete(synchronize_session=False)

    token = generate_secure_token(32)
    link = QrLoginLink(
        user_id=current_user.id,
        token_hash=hash_token(token),
        expires_at=now + timedelta(seconds=QR_LOGIN_TTL_SECONDS),
        created_at=now,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return {
        "id": link.id,
        "login_url": f"{settings.frontend_public_origin}/?qrLoginToken={quote(token)}",
        "expires_at": link.expires_at,
        "ttl_seconds": QR_LOGIN_TTL_SECONDS,
    }


@router.get("/qr-login-links/{link_id}/status", response_model=QrLoginStatusOut)
def qr_login_link_status(
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = db.query(QrLoginLink).filter(QrLoginLink.id == link_id, QrLoginLink.user_id == current_user.id).first()
    now = datetime.utcnow()
    if not link:
        return {"status": "missing"}
    if link.expires_at <= now:
        db.delete(link)
        db.commit()
        return {"status": "expired"}
    return {"status": "pending"}


@router.post("/qr-login/consume", response_model=UserOut)
def consume_qr_login_link(
    payload: QrLoginConsumeIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token_hash = hash_token(payload.token.strip())
    link = db.query(QrLoginLink).filter(QrLoginLink.token_hash == token_hash).with_for_update().first()
    now = datetime.utcnow()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR-ссылка входа не найдена.")
    if link.expires_at <= now:
        db.delete(link)
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR-ссылка входа истекла.")

    user = db.query(User).filter(User.id == link.user_id).first()
    db.delete(link)
    db.commit()
    if not user or user.blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь недоступен.")

    issue_session_pair(user, db, response, request)
    return user


@router.get("/oauthsky/config")
def oauthsky_public_config():
    enabled = oauthsky_configured()
    portal = settings.oauthsky_portal_url if enabled else ""
    return {"enabled": enabled, "portal_url": portal}
