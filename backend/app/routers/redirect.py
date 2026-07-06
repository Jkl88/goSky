from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_optional_user
from ..inactive_page import phrase_cookie_name, pick_phrase, render_inactive_page
from ..link_logic import inactive_kind, is_link_active, parse_device_type, request_ip_address
from ..models import LinkClick, ShortLink, User
from ..oauthsky_client import oauthsky_configured
from ..password_page import build_password_html_response
from ..redirect_password import is_redirect_unlocked, set_redirect_unlock_cookie
from ..security import verify_password
from ..slug import is_valid_slug

router = APIRouter(tags=["redirect"])


def _login_redirect(return_path: str) -> RedirectResponse:
    front = settings.frontend_public_origin.rstrip("/")
    if oauthsky_configured():
        q = quote(return_path, safe="")
        return RedirectResponse(
            url=f"{front}/api/auth/oauthsky/start?return_to={q}",
            status_code=status.HTTP_302_FOUND,
        )
    return RedirectResponse(url=f"{front}/?login_required=1", status_code=status.HTTP_302_FOUND)


def _inactive_response(link: ShortLink, request: Request, user: User | None) -> HTMLResponse:
    kind = inactive_kind(link) or "disabled"
    cookie_name = phrase_cookie_name(link.slug)
    try:
        phrase_index = int(request.cookies.get(cookie_name, "0"))
    except ValueError:
        phrase_index = 0
    phrase, next_index = pick_phrase(kind, phrase_index)
    html = render_inactive_page(
        slug=link.slug,
        kind=kind,
        phrase=phrase,
        home_url=settings.frontend_public_origin.rstrip("/"),
        show_home_button=user is not None,
    )
    response = HTMLResponse(content=html, status_code=status.HTTP_410_GONE)
    response.set_cookie(
        key=cookie_name,
        value=str(next_index),
        max_age=365 * 24 * 3600,
        path="/",
        samesite="lax",
        httponly=True,
        secure=settings.cookie_secure,
    )
    return response


def _password_response(link: ShortLink, request: Request, *, error: str | None = None) -> HTMLResponse:
    return build_password_html_response(
        link,
        request,
        context="redirect",
        form_action=f"/{link.slug}",
        error=error,
    )


def _get_link_or_404(slug: str, db: Session) -> ShortLink:
    if not is_valid_slug(slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    link = db.query(ShortLink).filter(ShortLink.slug == slug).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    return link


def _record_click_and_redirect(link: ShortLink, request: Request, db: Session) -> RedirectResponse:
    user_agent = (request.headers.get("user-agent") or "")[:512] or None
    ip_address = request_ip_address(request)
    device_type = parse_device_type(user_agent)

    link.click_count += 1
    link.updated_at = datetime.utcnow()
    db.add(
        LinkClick(
            link_id=link.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
        )
    )
    db.add(link)
    db.commit()
    return RedirectResponse(url=link.target_url, status_code=status.HTTP_302_FOUND)


def _handle_redirect(link: ShortLink, request: Request, db: Session, user: User | None):
    if link.is_private and user is None:
        return _login_redirect(f"/{link.slug}")
    if link.is_private and link.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к приватной ссылке.")

    if not is_link_active(link):
        return _inactive_response(link, request, user)

    if link.redirect_password_hash and not is_redirect_unlocked(link, request):
        return _password_response(link, request)

    return _record_click_and_redirect(link, request, db)


@router.get("/{slug}")
def redirect_short_link(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    link = _get_link_or_404(slug, db)
    return _handle_redirect(link, request, db, user)


@router.post("/{slug}")
async def unlock_redirect_short_link(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    link = _get_link_or_404(slug, db)
    if not is_link_active(link):
        return _inactive_response(link, request, user)
    if not link.redirect_password_hash:
        return _handle_redirect(link, request, db, user)

    form = await request.form()
    password = str(form.get("password") or "")
    if not password or not verify_password(password, link.redirect_password_hash):
        return _password_response(link, request, error="Неверный пароль. Попробуйте ещё раз.")

    response = RedirectResponse(url=f"/{link.slug}", status_code=status.HTTP_303_SEE_OTHER)
    set_redirect_unlock_cookie(response, link)
    return response


@router.get("/{slug}/vq")
def redirect_view_page(slug: str):
    if not is_valid_slug(slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена.")
    front = settings.frontend_public_origin.rstrip("/")
    return RedirectResponse(url=f"{front}/{slug}/vq", status_code=status.HTTP_302_FOUND)
