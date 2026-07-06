import re
import secrets

SLUG_MAX_LENGTH = 12
SLUG_MIN_CUSTOM_LENGTH = 3
SLUG_PATTERN = re.compile(r"^[A-Za-z0-9$@!%#]{1,12}$")
CUSTOM_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9$@!%#]{3,12}$")
SLUG_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz0123456789$@!%#"
DEFAULT_SLUG_LENGTH = 6
RESERVED_SLUGS = frozenset(
    {
        "api",
        "assets",
        "static",
        "health",
        "favicon.ico",
        "robots.txt",
        "links",
        "sessions",
        "share",
    }
)


def is_valid_slug(value: str) -> bool:
    if not value or value.lower() in RESERVED_SLUGS:
        return False
    return bool(SLUG_PATTERN.fullmatch(value))


def is_valid_custom_slug(value: str) -> bool:
    if not value or value.lower() in RESERVED_SLUGS:
        return False
    return bool(CUSTOM_SLUG_PATTERN.fullmatch(value))


def custom_slug_error(value: str) -> str | None:
    if not value:
        return "Укажите код ссылки"
    if value.lower() in RESERVED_SLUGS:
        return "Этот код зарезервирован"
    if not CUSTOM_SLUG_PATTERN.fullmatch(value):
        return "3–12 символов: цифры, латиница и $ @ ! % #"
    return None


def generate_random_slug(length: int = DEFAULT_SLUG_LENGTH) -> str:
    return "".join(secrets.choice(SLUG_CHARS) for _ in range(length))

