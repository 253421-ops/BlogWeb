"""Markdown -> HTML con componentes editoriales.

Seguridad: el HTML crudo se desactiva (anti-XSS) y los enlaces peligrosos como javascript: se bloquean.
Todo lo «especial» se escribe con una sintaxis simple y el generador produce el HTML:

  [^nota: texto]            nota al margen (sidenote)
  >> frase                  cita destacada (pull quote)
  :::info Título … :::      caja de concepto (también :::tip y :::warning)
  :::wide … :::             contenedor ancho (imagen + pie de foto, o una línea «iframe: https://…»)
  ![pie](url#wide)          imagen ancha con pie de foto
  ```python … ```           código con etiqueta del lenguaje y botón «Copiar»
"""
import re

from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml

OPEN, CLOSE = "", ""        # marcas privadas: nunca salen del texto de la usuaria (se borran al entrar)
CALLOUT = re.compile(r"^:::(info|tip|warning|wide)(?:[ \t]+(.*))?$")
FENCE = re.compile(r"^\s{0,3}(```|~~~)")
SIDENOTE = re.compile(r"\[\^nota:\s*((?:[^\[\]]|\[[^\]]*\]\([^)]*\))+)\]")
IFRAME = re.compile(r"^iframe:\s*(https://[^\s\"'<>]+)\s*$", re.I)
WIDE_IMG = re.compile(r'<p><img src="([^"]+)#wide" alt="([^"]*)"(?: title="[^"]*")? ?/?></p>')
ICONS = {  # íconos SVG simples (sin dependencias)
    "info": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 11v6M12 7.5v.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    "tip": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "warning": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 2.5 20h19L12 3zM12 10v5M12 17.5v.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}
DEFAULT_TITLE = {"info": "Idea clave", "tip": "Consejo", "warning": "Ojo"}


def _slug(text: str, seen: dict) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", re.sub(r"[̀-ͯ]", "", __import__("unicodedata").normalize("NFD", text.lower()))).strip("-") or "seccion"
    n = seen.get(base, 0)
    seen[base] = n + 1
    return base if n == 0 else f"{base}-{n + 1}"


def _fence(tokens, idx, options, env):
    tok = tokens[idx]
    info = tok.info.strip().split()[0] if tok.info.strip() else ""
    lang = re.sub(r"[^A-Za-z0-9_+#.-]", "", info)[:20]
    label = (lang or "texto").upper()
    return (f'<div class="codeblock"><div class="codebar"><span class="lang">{escapeHtml(label)}</span>'
            f'<button type="button" class="copy" data-copy>Copiar</button></div>'
            f'<pre><code class="language-{escapeHtml(lang.lower() or "text")}">{escapeHtml(tok.content)}</code></pre></div>\n')


def _heading_open(tokens, idx, options, env):
    tok = tokens[idx]
    text = tokens[idx + 1].content if idx + 1 < len(tokens) else ""
    ident = _slug(re.sub(r"[`*_]", "", text), env.setdefault("ids", {}))
    tok.attrSet("id", ident)
    if tok.tag in ("h2", "h3"):
        env.setdefault("toc", []).append({"level": int(tok.tag[1]), "id": ident, "text": re.sub(r"[`*_]", "", text)})
    return "<%s id=\"%s\">" % (tok.tag, escapeHtml(ident))


_md = MarkdownIt("commonmark", {"html": False})
_md.renderer.rules["fence"] = _fence
_md.renderer.rules["heading_open"] = _heading_open


def _callout(kind: str, title: str, inner: str) -> str:
    if kind == "wide":
        return _wide(inner)
    title = (title or "").strip() or DEFAULT_TITLE[kind]
    return (f'<div class="callout {kind}" role="note"><div class="callout-t">{ICONS[kind]}<span>{escapeHtml(title)}</span></div>'
            f'<div class="callout-b">{_render(inner)[0]}</div></div>')


def _wide(inner: str) -> str:
    """Contenedor ancho: una línea «iframe: https://…» o una imagen; el resto del texto es el pie de foto."""
    frames, rest = [], []
    for line in inner.splitlines():
        m = IFRAME.match(line.strip())
        (frames if m else rest).append(m.group(1) if m else line)
    media = "".join(f'<iframe src="{escapeHtml(u)}" loading="lazy" referrerpolicy="no-referrer" sandbox="allow-scripts allow-same-origin allow-popups" title="Contenido interactivo"></iframe>' for u in frames)
    body = _render("\n".join(rest))[0]
    img = re.match(r"\s*(<p><img [^>]*></p>)(.*)$", body, re.S)
    if img and not media:
        media, caption = img.group(1).replace("<p>", "").replace("</p>", ""), img.group(2).strip()
    else:
        caption = body.strip() if media else body
    cap = f"<figcaption>{re.sub(r'</?p>', '', caption).strip()}</figcaption>" if re.sub(r"\s|<[^>]+>", "", caption) else ""
    return f'<figure class="wide">{media}{cap}</figure>'


def _prepare(text: str, blocks: list, notes: list) -> str:
    """Saca del texto lo especial (cajas, citas, notas) y deja marcas; así markdown-it no lo toca."""
    out, lines, fenced, i = [], text.replace(OPEN, "").replace(CLOSE, "").replace("\r\n", "\n").split("\n"), None, 0
    while i < len(lines):
        line = lines[i]
        fm = FENCE.match(line)
        if fenced:
            out.append(line)
            if fm and fm.group(1) == fenced:
                fenced = None
            i += 1
            continue
        if fm:
            fenced = fm.group(1)
            out.append(line)
            i += 1
            continue
        cm = CALLOUT.match(line.strip())
        if cm:
            inner, i = [], i + 1
            while i < len(lines) and lines[i].strip() != ":::":
                inner.append(lines[i])
                i += 1
            blocks.append(_callout(cm.group(1), cm.group(2) or "", "\n".join(inner)))
            out += ["", f"{OPEN}B{len(blocks) - 1}{CLOSE}", ""]
            i += 1
            continue
        pq = re.match(r"^>>\s+(.+)$", line)
        if pq:
            blocks.append(f'<aside class="pullquote"><p>{_md.renderInline(pq.group(1).strip())}</p></aside>')
            out += ["", f"{OPEN}B{len(blocks) - 1}{CLOSE}", ""]
            i += 1
            continue
        parts = re.split(r"(`[^`]*`)", line)               # las notas no se buscan dentro de `código`
        for k in range(0, len(parts), 2):
            def put(m):
                notes.append(m.group(1).strip())
                return f"{OPEN}S{len(notes) - 1}{CLOSE}"
            parts[k] = SIDENOTE.sub(put, parts[k])
        out.append("".join(parts))
        i += 1
    return "\n".join(out)


def _render(text: str) -> tuple[str, list]:
    blocks: list[str] = []
    notes: list[str] = []
    env: dict = {}
    html = _md.render(_prepare(text or "", blocks, notes), env)
    html = re.sub(OPEN + r"B(\d+)" + CLOSE, lambda m: blocks[int(m.group(1))], html)
    html = re.sub(r"<p>(<(?:div|figure|aside)\b.*?</(?:div|figure|aside)>)</p>", r"\1", html, flags=re.S)
    html = WIDE_IMG.sub(lambda m: f'<figure class="wide"><img src="{m.group(1)}" alt="{m.group(2)}" loading="lazy"><figcaption>{m.group(2)}</figcaption></figure>', html)

    def side(m):
        n = int(m.group(1))
        sid = f"sn{n + 1}"
        return (f'<label for="{sid}" class="sn-num" aria-label="Nota {n + 1}"></label><input type="checkbox" id="{sid}" class="margin-toggle">'
                f'<span class="sidenote">{_md.renderInline(notes[n])}</span>')
    html = re.sub(OPEN + r"S(\d+)" + CLOSE, side, html)
    return html, env.get("toc", [])


def render_markdown(text: str) -> str:
    return _render(text)[0]


def render_article(text: str) -> tuple[str, list[dict]]:
    """(HTML del artículo, índice de encabezados ## y ###)."""
    return _render(text)


def extract_clean_excerpt(md_text: str, max_len: int = 150) -> str:
    """Texto plano y corto para las tarjetas: sin imágenes, enlaces, encabezados, negritas ni bloques de código."""
    t = md_text or ""
    t = re.sub(r"(```|~~~).*?(?:\1|\Z)", " ", t, flags=re.S)            # bloques de código (también el que quedó sin cerrar)
    t = re.sub(r"!\[[^\]]*\](?:\([^)]*\)?)?", " ", t)                    # imágenes ![alt](url) y las cortadas a medias
    t = re.sub(r"!\[[^\]]*$", " ", t)
    t = re.sub(r"\[\^nota:[^\]]*\]", " ", t)                             # notas al margen
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)                       # [texto](url) -> texto
    t = re.sub(r"^\s*:::\w*.*$", " ", t, flags=re.M)                     # cajas :::info
    t = re.sub(r"<[^>]+>", " ", t)                                       # etiquetas HTML sueltas
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)                  # encabezados
    t = re.sub(r"^\s*>+\s?", "", t, flags=re.M)                          # citas y citas destacadas
    t = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", t, flags=re.M)           # viñetas
    t = re.sub(r"(\*\*|__|~~|`)", "", t)                                 # negritas, tachado, código en línea
    t = re.sub(r"(?<!\w)[*_]|[*_](?!\w)", "", t)                         # cursivas
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= max_len:
        return t
    cut = t[:max_len - 1].rsplit(" ", 1)[0] or t[:max_len - 1]
    return cut.rstrip(" ,;:.-") + "…"
