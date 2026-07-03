import re
import secrets

SLUG_PATTERN = re.compile(r"^[A-Za-z0-9$@!%#]{1,6}$")
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
    }
)


def is_valid_slug(value: str) -> bool:
    if not value or value.lower() in RESERVED_SLUGS:
        return False
    return bool(SLUG_PATTERN.fullmatch(value))


def generate_random_slug(length: int = DEFAULT_SLUG_LENGTH) -> str:
    return "".join(secrets.choice(SLUG_CHARS) for _ in range(length))

