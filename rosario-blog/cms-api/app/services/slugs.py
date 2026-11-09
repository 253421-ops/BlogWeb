import re
import unicodedata
from collections.abc import Callable


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower() or "item"


def make_slug(base: str, exists: Callable[[str], bool]) -> str:
    """Devuelve `base` o `base-2`, `base-3`... hasta encontrar uno libre."""
    slug, n = base, 2
    while exists(slug):
        slug = f"{base}-{n}"
        n += 1
    return slug
