"""Markdown -> HTML. El HTML crudo se desactiva (anti-XSS) y los enlaces peligrosos como javascript: se bloquean."""
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False})


def render_markdown(text: str) -> str:
    return _md.render(text)
