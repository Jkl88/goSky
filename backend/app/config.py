from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/gosky"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    session_cookie_name: str = "gosky_session"
    refresh_cookie_name: str = "gosky_refresh"
    session_expire_minutes: int = 15
    refresh_expire_days: int = 30
    cookie_secure: bool = False

    oauthsky_enabled: bool = False
    oauthsky_url: str = ""
    oauthsky_internal_url: str = ""
    oauthsky_client_id: str = ""
    oauthsky_client_secret: str = ""
    oauthsky_redirect_uri: str = ""

    frontend_origin: str = Field(...)
    public_base_url: str = ""

    @property
    def oauthsky_portal_url(self) -> str:
        return (self.oauthsky_url or "").strip().rstrip("/")

    @property
    def oauthsky_api_base_url(self) -> str:
        internal = (self.oauthsky_internal_url or "").strip().rstrip("/")
        if internal:
            return internal
        return self.oauthsky_portal_url

    @property
    def oauthsky_redirect_uri_resolved(self) -> str:
        explicit = (self.oauthsky_redirect_uri or "").strip()
        if explicit:
            return explicit
        if self.oauthsky_enabled and self.frontend_public_origin:
            return f"{self.frontend_public_origin.rstrip('/')}/api/auth/oauthsky/callback"
        return ""

    @property
    def frontend_public_origin(self) -> str:
        raw = (self.frontend_origin or "").strip()
        if not raw:
            return raw
        if not raw.startswith("//") and "://" not in raw:
            raw = f"https://{raw}"
        parsed = urlsplit(raw)
        if not parsed.netloc and parsed.path and not parsed.scheme:
            raw = f"https://{parsed.path}"
        return raw.rstrip("/")

    @property
    def short_link_base_url(self) -> str:
        raw = (self.public_base_url or "").strip()
        if raw:
            if not raw.startswith("//") and "://" not in raw:
                raw = f"https://{raw}"
            return raw.rstrip("/")
        return self.frontend_public_origin

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
