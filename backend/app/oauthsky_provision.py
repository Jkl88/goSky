"""Создание/привязка локального пользователя после входа через OAuthSky."""

import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import User
from .security import hash_password


def provision_user_from_oauthsky(db: Session, sky_user: dict) -> User:
    uid = int(sky_user["id"])
    login = str(sky_user.get("login") or "").strip()
    email = str(sky_user.get("email") or "").strip().lower()
    blocked = bool(sky_user.get("blocked"))
    if blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь заблокирован в OAuthSky.")
    if not login or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неполный профиль OAuthSky.")

    row = db.query(User).filter(User.oauthsky_user_id == uid).first()
    if row:
        row.login = login
        row.email = email
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    by_email = db.query(User).filter(User.email == email).first()
    if by_email:
        if by_email.oauthsky_user_id and int(by_email.oauthsky_user_id) != uid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email уже привязан к другому аккаунту OAuthSky.",
            )
        by_email.oauthsky_user_id = uid
        by_email.login = login
        db.add(by_email)
        db.commit()
        db.refresh(by_email)
        return by_email

    by_login = db.query(User).filter(User.login == login).first()
    if by_login:
        if by_login.oauthsky_user_id and int(by_login.oauthsky_user_id) != uid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Логин уже занят другим аккаунтом.",
            )
        by_login.oauthsky_user_id = uid
        by_login.email = email
        db.add(by_login)
        db.commit()
        db.refresh(by_login)
        return by_login

    user = User(
        login=login,
        email=email,
        password_hash=hash_password(secrets.token_urlsafe(32)),
        oauthsky_user_id=uid,
        role="user",
        blocked=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
