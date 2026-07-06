from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user, get_optional_user
from ..link_logic import device_label, inactive_reason, is_link_active
from ..models import LinkClick, ShortLink, User
from ..schemas import (
    LinkClickOut,
    LinkStatsOut,
    ShortLinkCreateIn,
    ShortLinkOut,
    ShortLinkUpdateIn,
    ShortLinkViewOut,
    SlugCheckOut,
)
from ..slug import custom_slug_error, generate_random_slug, is_valid_custom_slug, is_valid_slug

router = APIRouter(prefix="/api/links", tags=["links"])

STATS_LIMIT = 200


def _link_urls(slug: str) -> tuple[str, str]:
    base = settings.short_link_base_url.rstrip("/")
    return f"{base}/{slug}", f"{base}/{slug}/vq"


def _resolve_expires_at(payload_expires_at: datetime | None, ttl_hours: int | None) -> datetime | None:
    if payload_expires_at is not None:
        return payload_expires_at
    if ttl_hours is not None:
        return datetime.utcnow() + timedelta(hours=ttl_hours)
    return None


def _to_out(link: ShortLink) -> ShortLinkOut:
    short_url, view_url = _link_urls(link.slug)
    active = is_link_active(link)
    return ShortLinkOut(
        id=link.id,
        slug=link.slug,
        target_url=link.target_url,
        title=link.title,
        is_private=link.is_private,
        is_enabled=link.is_enabled,
        click_count=link.click_count,
        expires_at=link.expires_at,
        max_clicks=link.max_clicks,
        is_active=active,
        inactive_reason=inactive_reason(link) if not active else None,
        created_at=link.created_at,
        updated_at=link.updated_at,
        short_url=short_url,
        view_url=view_url,
    )


def _check_link_access(link: ShortLink, user: User | None) -> None:
    if not link.is_private:
        return
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Приватная ссылка — требуется вход.")
    if link.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к приватной ссылке.")


def _get_owned_link(db: Session, slug: str, user: User) -> ShortLink:
    if not is_valid_slug(slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    link = db.query(ShortLink).filter(ShortLink.slug == slug).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    if link.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа.")
    return link


@router.get("", response_model=list[ShortLinkOut])
def list_my_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    links = (
        db.query(ShortLink)
        .filter(ShortLink.user_id == current_user.id)
        .order_by(ShortLink.created_at.desc())
        .all()
    )
    return [_to_out(link) for link in links]


@router.get("/check-slug/{slug}", response_model=SlugCheckOut)
def check_slug_available(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    reason = custom_slug_error(slug.strip())
    if reason:
        return SlugCheckOut(available=False, reason=reason)
    exists = db.query(ShortLink.id).filter(ShortLink.slug == slug.strip()).first()
    if exists:
        return SlugCheckOut(available=False, reason="Такой код уже занят")
    return SlugCheckOut(available=True)


@router.post("", response_model=ShortLinkOut, status_code=status.HTTP_201_CREATED)
def create_link(
    payload: ShortLinkCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expires_at = _resolve_expires_at(payload.expires_at, payload.ttl_hours)
    if expires_at is not None and expires_at <= datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Срок действия должен быть в будущем.")

    if payload.slug:
        slug = payload.slug
        reason = custom_slug_error(slug)
        if reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
        existing = db.query(ShortLink.id).filter(ShortLink.slug == slug).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Такой код уже занят")
        link = ShortLink(
            user_id=current_user.id,
            slug=slug,
            target_url=payload.target_url,
            title=payload.title,
            is_private=payload.is_private,
            expires_at=expires_at,
            max_clicks=payload.max_clicks,
        )
        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Такой код уже занят") from None
        db.refresh(link)
        return _to_out(link)

    for _ in range(32):
        slug = generate_random_slug()
        if not is_valid_slug(slug):
            continue
        link = ShortLink(
            user_id=current_user.id,
            slug=slug,
            target_url=payload.target_url,
            title=payload.title,
            is_private=payload.is_private,
            expires_at=expires_at,
            max_clicks=payload.max_clicks,
        )
        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        db.refresh(link)
        return _to_out(link)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Не удалось сгенерировать уникальный код ссылки. Попробуйте ещё раз.",
    )


@router.get("/{slug}/stats", response_model=LinkStatsOut)
def link_stats(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = _get_owned_link(db, slug, current_user)
    clicks = (
        db.query(LinkClick)
        .filter(LinkClick.link_id == link.id)
        .order_by(LinkClick.clicked_at.desc())
        .limit(STATS_LIMIT)
        .all()
    )
    unique_ips = (
        db.query(func.count(func.distinct(LinkClick.ip_address)))
        .filter(LinkClick.link_id == link.id, LinkClick.ip_address.isnot(None))
        .scalar()
        or 0
    )
    device_rows = (
        db.query(LinkClick.device_type, func.count(LinkClick.id))
        .filter(LinkClick.link_id == link.id)
        .group_by(LinkClick.device_type)
        .all()
    )
    device_breakdown = {device_label(dt): int(cnt) for dt, cnt in device_rows}
    active = is_link_active(link)
    return LinkStatsOut(
        slug=link.slug,
        click_count=link.click_count,
        unique_ips=int(unique_ips),
        is_active=active,
        inactive_reason=inactive_reason(link) if not active else None,
        expires_at=link.expires_at,
        max_clicks=link.max_clicks,
        device_breakdown=device_breakdown,
        clicks=[
            LinkClickOut(
                id=c.id,
                ip_address=c.ip_address,
                user_agent=c.user_agent,
                device_type=c.device_type,
                device_label=device_label(c.device_type),
                clicked_at=c.clicked_at,
            )
            for c in clicks
        ],
    )


@router.get("/{slug}/view", response_model=ShortLinkViewOut)
def view_link(
    slug: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not is_valid_slug(slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    link = db.query(ShortLink).filter(ShortLink.slug == slug).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")

    _check_link_access(link, user)
    short_url, view_url = _link_urls(link.slug)
    is_owner = user is not None and link.user_id == user.id
    active = is_link_active(link)
    return ShortLinkViewOut(
        slug=link.slug,
        target_url=link.target_url,
        title=link.title,
        is_private=link.is_private,
        is_enabled=link.is_enabled,
        click_count=link.click_count,
        expires_at=link.expires_at,
        max_clicks=link.max_clicks,
        is_active=active,
        inactive_reason=inactive_reason(link) if not active else None,
        short_url=short_url,
        view_url=view_url,
        is_owner=is_owner,
        can_edit=is_owner,
    )


@router.get("/{slug}", response_model=ShortLinkOut)
def get_link(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = _get_owned_link(db, slug, current_user)
    return _to_out(link)


@router.patch("/{slug}", response_model=ShortLinkOut)
def update_link(
    slug: str,
    payload: ShortLinkUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = _get_owned_link(db, slug, current_user)

    if payload.target_url is not None:
        link.target_url = payload.target_url
    if payload.title is not None:
        link.title = payload.title or None
    if payload.is_private is not None:
        link.is_private = payload.is_private
    if payload.is_enabled is not None:
        link.is_enabled = payload.is_enabled

    if payload.clear_expires_at:
        link.expires_at = None
    elif payload.ttl_hours is not None:
        link.expires_at = datetime.utcnow() + timedelta(hours=payload.ttl_hours)
    elif payload.expires_at is not None:
        if payload.expires_at <= datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Срок действия должен быть в будущем.")
        link.expires_at = payload.expires_at

    if payload.clear_max_clicks:
        link.max_clicks = None
    elif payload.max_clicks is not None:
        link.max_clicks = payload.max_clicks

    link.updated_at = datetime.utcnow()
    db.add(link)
    db.commit()
    db.refresh(link)
    return _to_out(link)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = _get_owned_link(db, slug, current_user)
    db.delete(link)
    db.commit()
    return None
