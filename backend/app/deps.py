from datetime import datetime

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User, UserSession
from .security import hash_token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> User:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация.")

    now = datetime.utcnow()
    session_row = db.query(UserSession).filter(
        UserSession.session_token_hash == hash_token(session_token),
        UserSession.revoked.is_(False),
    ).first()
    if not session_row or session_row.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия истекла или недействительна.")

    user = db.query(User).filter(User.id == int(session_row.user_id)).first()
    if not user or user.blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь недоступен.")

    session_row.last_seen_at = now
    db.add(session_row)
    db.commit()
    db.refresh(user)
    request.state.user_session = session_row
    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> User | None:
    if not session_token:
        return None
    try:
        return get_current_user(request, db, session_token)
    except HTTPException:
        return None
