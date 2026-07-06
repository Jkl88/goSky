"""Валидация и нормализация целевых URL (любые безопасные схемы)."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

BLOCKED_SCHEMES = frozenset({"javascript", "data", "vbscript", "file"})
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*$")


def normalize_target_url(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("URL не может быть пустым.")

    if "://" not in raw and not raw.lower().startswith("mailto:") and not raw.lower().startswith("tel:"):
        # Без схемы: example.com, t.me/channel
        if re.match(r"^[\w.-]+\.[\w.-]+", raw) or raw.startswith("t.me/"):
            raw = f"https://{raw}"

    parsed = urlsplit(raw)
    scheme = (parsed.scheme or "").lower()
    if not scheme:
        raise ValueError("Укажите ссылку со схемой: http://, https://, ftp://, tg://, mailto:, tel: и др.")

    if scheme in BLOCKED_SCHEMES:
        raise ValueError("Такая схема URL не поддерживается.")

    if not _SCHEME_RE.match(parsed.scheme):
        raise ValueError("Некорректная схема URL.")

    after_scheme = raw.split(":", 1)[1]
    if not after_scheme:
        raise ValueError("URL слишком короткий.")

    return raw


def mask_target_url(value: str) -> str:
    """Скрывает путь и параметры, оставляя только схему и домен."""
    raw = (value or "").strip()
    if not raw:
        return "********"

    parsed = urlsplit(raw)
    scheme = (parsed.scheme or "").lower()

    if scheme in ("http", "https", "ftp") and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/********"

    if scheme == "mailto":
        addr = raw.split(":", 1)[1] if ":" in raw else raw
        if "@" in addr:
            host = addr.rsplit("@", 1)[1]
            return f"mailto:********@{host}"
        return "mailto:********"

    if scheme:
        return f"{parsed.scheme or scheme}://********"

    return "********"
