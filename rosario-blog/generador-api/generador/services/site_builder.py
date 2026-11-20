"""EL GENERADOR: 1) EXTRAER lo publicado del CMS  2) RENDERIZAR todas las páginas en memoria  3) PUBLICAR los archivos.
Si falla algo antes del paso 3, el sitio anterior queda intacto."""
import base64
import html
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from common.markdown import extract_clean_excerpt, render_article, render_markdown
from generador.services import sections as sec
from generador.services.scene import build_scene
from generador.services.styles import CSS, SITE_JS


class BuildError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def from_bundle(bundle: dict):
    """Traduce el contenido que envía el CMS (camelCase) a lo que usa el renderizador."""
    posts = [{"post_id": p["id"], "title": p["title"], "slug": p["slug"], "body": p.get("content") or "", "summary": p.get("excerpt"),
              "category_id": p.get("categoryId"), "cover": p.get("coverUrl"), "status": "PUBLICADO", "published_at": p.get("publishedAt") or p["createdAt"], "tags": []}
             for p in bundle.get("posts", []) if p.get("status") == "published"]
    categories = [{"category_id": c["id"], "name": c["name"]} for c in bundle.get("categories", [])]
    pages = [p for p in bundle.get("pages", []) if p.get("status") == "published"]
    return posts, categories, pages

BASE_VARS = ("--bg:#070d2b;--bg2:#0e1b4d;--surface:rgba(255,255,255,.06);--text:#eef1ff;--text-muted:#aeb9e6;--accent:#f5c451;--accent-text:#f5c451;--on-accent:#14193a;"
             "--border:rgba(255,255,255,.14);--hero:#ffffff;--sky1:#050a24;--sky2:#10265e;--sky3:#4d86a8;--moon:#f8e7a0;--mtn1:#1d3b52;--mtn2:#11261f;--tree:#0b1c15;--house:#141a33;"
             "--window:#ffd166;--ground1:#1d3b22;--ground2:#0b1d12;--glow:#f5d36b;--paper:#fbf1d3;--dock:rgba(7,13,43,.9);--hero-shadow:rgba(0,0,0,.5);--code-bg:rgba(0,0,0,.38);"
             "--font-head:'Dancing Script','Segoe Script',cursive;--font-body:'Inter',system-ui,sans-serif;--font-mono:'JetBrains Mono',ui-monospace,monospace;"
             "--text-base:18px;--scale-ratio:1.25;--step-0:18.00px;--step-1:22.50px;--step-2:28.13px;--step-3:35.16px;--step-4:43.95px;--step-5:54.93px")
# el CSS del tema sólo puede traer variables (una o dos paletas), nada más
SAFE_VARS = re.compile(r"^(?::root(?:\[data-mode=(?:light|dark)\])?\{[A-Za-z0-9#,'\-;:. ()]{0,4500}\}){1,2}$")
SAFE_FONTS = re.compile(r"^https://fonts\.googleapis\.com/css2\?[A-Za-z0-9+:;=&@.,_-]{1,600}$")
DEFAULT_FONTS = "https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap"
SAFE_URL = re.compile(r"^https?://[^\s\"'<>]+$")
MODE_SCRIPT = ("(function(){var r=document.documentElement;try{var m=localStorage.getItem('brisa-mode');if(m!=='light'&&m!=='dark')"
               "m=r.dataset.default||(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark');r.dataset.mode=m}catch(e){}})();")
TOGGLE = ('<button type="button" class="modebtn" data-mode-toggle aria-label="Cambiar de modo"><svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" stroke-width="2"/>'
          '<path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
          '<svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></button>')
EXTRA_CSS = (".prose{line-height:1.8}.prose p{margin:0 0 14px}.prose img{max-width:100%;border-radius:16px}.prose h2{font-size:36px;margin:26px 0 8px}.prose h3{font-size:28px;margin:20px 0 6px}"
             ".prose code{background:var(--border);padding:2px 6px;border-radius:6px;font-family:var(--font-mono)}.prose blockquote{margin:16px 0;padding:4px 18px;border-left:3px solid var(--accent);color:var(--text-muted)}")

LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M21 3a13 13 0 1 0 8 22A11 11 0 0 1 21 3z" fill="var(--accent)"/></svg>'
TRACKER = """(function(){var s=document.currentScript,ep=s&&s.dataset.endpoint;if(!ep||navigator.doNotTrack==='1')return;
function id(){return crypto.randomUUID()}function keep(st,k){try{var v=st.getItem(k);if(!v){v=id();st.setItem(k,v)}return v}catch(e){return id()}}
var sid=keep(sessionStorage,'sid'),vid=keep(localStorage,'vid'),slug=document.body.dataset.slug;
function send(type,x){var e={event_id:id(),type:type,session_id:sid,visitor_id:vid,path:location.pathname};if(slug)e.post_slug=slug;for(var k in x)e[k]=x[k];
fetch(ep,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({events:[e]}),keepalive:true}).catch(function(){})}
var ref={};try{var r=new URL(document.referrer);if(r.host!==location.host)ref.referrer_host=r.host}catch(e){}send('page_view',ref);
var done={};addEventListener('scroll',function(){var d=document.documentElement,m=d.scrollHeight-innerHeight,p=m<=0?100:Math.round(scrollY/m*100);
[25,50,75,100].forEach(function(t){if(p>=t&&!done[t]){done[t]=1;send('scroll_depth',{value:t})}})},{passive:true});
var t0=Date.now(),sent=0;function leave(){if(sent)return;var sec=Math.min(3600,Math.round((Date.now()-t0)/1000));if(sec>0){sent=1;send('time_on_page',{value:sec})}}
addEventListener('pagehide',leave);document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')leave()});
document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('a[href]');if(a&&a.host&&a.host!==location.host)send('link_click',{target_host:a.host})})})();"""


SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,120}\.(jpg|png|webp|gif)$")


def localize_media(bundle: dict, base: str, posts: list[dict], pages: list[dict]) -> dict[str, bytes]:
    """Guarda las imágenes del paquete dentro del sitio y reescribe sus direcciones en los textos."""
    files: dict[str, bytes] = {}
    for m in bundle.get("media") or []:
        name = m.get("name") or ""
        if not SAFE_NAME.match(name) or not m.get("url"):
            continue
        try:
            files[f"assets/media/{name}"] = base64.b64decode(m["data"], validate=True)
        except Exception:  # noqa: BLE001
            continue
        pat = re.compile(r"(?:https?://[^/\s)\"']+)?" + re.escape(m["url"]))
        for item in posts:
            item["body"] = pat.sub(f"{base}/assets/media/{name}", item["body"])
            if item.get("cover"):
                item["cover"] = pat.sub(f"{base}/assets/media/{name}", item["cover"])
        for item in pages:
            item["content"] = pat.sub(f"{base}/assets/media/{name}", item.get("content") or "")
    return files


@lru_cache(maxsize=1)
def _scene() -> str:
    return build_scene()


def render_site(posts: list[dict], categories: list[dict], cfg, pages: list[dict] | None = None, bundle: dict | None = None) -> dict[str, str | bytes]:
    bundle = bundle or {}
    base = cfg.site_base.rstrip("/")
    cat = {c["category_id"]: c["name"] for c in categories}
    posts = sorted((p for p in posts if p.get("status") == "PUBLICADO"), key=lambda p: p.get("published_at", ""), reverse=True)
    e = html.escape
    blog = bundle.get("blog") or {}
    title = blog.get("name") or cfg.site_title
    desc = blog.get("description") or cfg.site_description
    theme = bundle.get("theme") or {}
    blog_tpl = theme.get("blog") if theme.get("blog") in ("tarjetas", "lista") else "tarjetas"
    mode = theme.get("mode") if theme.get("mode") in ("light", "dark") else "dark"      # modo por defecto elegido en el CMS (el lector puede cambiarlo)
    fonts = theme.get("fonts_url") if SAFE_FONTS.match(theme.get("fonts_url") or "") else DEFAULT_FONTS
    tcss = bundle.get("theme_css") or ""
    tcss = tcss if SAFE_VARS.match(tcss) else ":root{" + BASE_VARS + "}"
    landing_url = (getattr(cfg, "landing_url", "") or "").strip()
    landing_url = landing_url if SAFE_URL.match(landing_url) else ""                  # sólo http(s); vacío = la portada de este mismo sitio
    home_href = landing_url or f"{base}/"
    home_attr = " data-landing" if landing_url else ""
    pages = [dict(g) for g in (pages or [])]
    posts = [dict(q) for q in posts]
    media = localize_media(bundle, base, posts, pages)
    about = next((g for g in pages if g.get("slug") == "sobre-mi"), None)
    others = [g for g in pages if g.get("type") != "landing" and g.get("slug") != "sobre-mi"]
    n = len(posts)
    plural = lambda k, one, many: f"{k} {one if k == 1 else many}"
    for q in posts:                                                   # resumen en texto plano: sin Markdown crudo en las tarjetas
        q["extract"] = extract_clean_excerpt(q.get("summary") or "") or extract_clean_excerpt(q["body"]) or "Leer la entrada completa."

    def dock(active: str) -> str:
        if active == "inicio":
            anchors = [("sobre-mi", "☾ Sobre mí"), ("dibujos", "🎨 Dibujos"), ("carrera", "⌬ Carrera"), ("textil", "❀ Textil"), ("proyectos", "☄ Proyectos"),
                       ("materias", "✎ Materias"), ("herramientas", "⚙ Herramientas"), ("pensamientos", "☁ Pensamientos"), ("blog", "✦ Blog")]
            first = f'<a href="{e(landing_url)}" data-landing>⌂ Inicio</a>' if landing_url else '<a href="#contenido">⌂ Inicio</a>'
            return ('<nav class="dock" aria-label="Principal">' + first + "".join(f'<a href="#{k}">{t}</a>' for k, t in anchors)
                    + f'<a href="{base}/blog/">Todas las entradas</a></nav>')
        items = [("inicio", home_href, "✦ Inicio"), ("blog", f"{base}/blog/", "✎ Blog")] + [(g["slug"], f"{base}/{g['slug']}/", e(g["title"])) for g in others]
        return '<nav class="dock" aria-label="Principal">' + "".join(
            f'<a href="{e(h)}"{home_attr if k == "inicio" else ""}{" aria-current=page" if k == active else ""}>{t}</a>' for k, h, t in items) + "</nav>"

    def scene_block(inner: str, compact: bool) -> str:
        return (f'<section class="scene{" compact" if compact else ""}">{_scene()}<div class="wrap" style="position:relative;z-index:2;display:flex;flex-direction:column;flex:1;width:100%">'
                f'<header class="top"><a class="brand" href="{e(home_href)}"{home_attr}>{LOGO}{e(title)}</a><div class="top-r"><span class="kicker">{e(desc)[:60]}</span>{TOGGLE}</div></header>{inner}</div></section>')

    def page(ttl: str, hero: str, body: str, active: str, slug: str | None = None, compact: bool = True, extra: str = "") -> str:
        return (f'<!doctype html><html lang="es" data-mode="{mode}" data-default="{mode}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<script>{MODE_SCRIPT}</script>'
                f'<title>{e(ttl)} · {e(title)}</title><meta name="description" content="{e(desc)}">'
                f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                f'<link href="{e(fonts)}" rel="stylesheet">'
                f'<link rel="stylesheet" href="{base}/assets/style.css"></head>'
                f'<body{f" data-slug={chr(34)}{e(slug)}{chr(34)}" if slug else ""}><a class="skip" href="#contenido">Saltar al contenido</a><div id="prog"></div>'
                f'{scene_block(hero, compact)}<main id="contenido" class="wrap">{body}<footer class="foot">{e(title)} · hecho con un CMS API-First</footer></main>{extra}{dock(active)}'
                f'<script src="{base}/assets/site.js" defer></script>'
                f'<script src="{base}/assets/tracker.js" data-endpoint="{e(cfg.metrics_url)}/api/v1/events" defer></script></body></html>')

    def card(p, big=False):
        extract = p["extract"]
        label = cat.get(p["category_id"], "") or "Entrada"
        mins = max(1, math.ceil(len(p["body"].split()) / 200))
        return (f'<a class="card{" big" if big else ""}" href="{base}/posts/{e(p["slug"])}/" data-cat="{e(label)}" data-t="{e((p["title"] + " " + extract).lower())}"><span class="chip">{e(label)}</span>'
                f'<h3>{e(p["title"])}</h3><p>{e(extract)}</p><span class="meta">{e(p["published_at"][:10])} · {mins} min de lectura</span><span class="more">Leer →</span></a>')

    files: dict = {"assets/style.css": tcss + "\n" + CSS + "\n" + EXTRA_CSS + sec.CSS, "assets/tracker.js": TRACKER, "assets/site.js": SITE_JS + "\n" + sec.JS}
    files.update(media)
    landing = next((g for g in pages if g.get("type") == "landing"), None)
    intro = render_markdown(landing["content"]) if landing and landing.get("content") else f"<p>{e(desc)}</p>"
    empty = '<p class="panel">Aún no hay entradas publicadas. Cuando publiques la primera, aparecerá aquí.</p>'

    # ---- portada ----
    hero = (f'<div class="hero-in"><div class="box"><span class="kicker">un diario de pequeños intentos</span><h1>{e(title)}</h1><div class="intro">{intro}</div>'
            f'<div class="btns"><a class="btn fill" href="#sobre-mi">Quién soy →</a><a class="btn" href="#carrera">¿Es para ti?</a><a class="btn" href="{base}/blog/">Leer el blog</a></div></div></div>')
    special, normal = sec.split_posts(posts, cat)
    about_img = sec.cover(about["content"]) if about and about.get("content") else None
    about_html = render_markdown(re.sub(r"!\[[^\]]*\]\([^)]*\)", "", about["content"])) if about and about.get("content") else None
    sections = sec.render_sections(base, special, normal, about_html, about_img, card, empty, len(posts))
    counts: dict[str, int] = {}
    for p in posts:
        counts[cat.get(p["category_id"], "") or "Entrada"] = counts.get(cat.get(p["category_id"], "") or "Entrada", 0) + 1
    files["index.html"] = page(title, hero, sections, "inicio", compact=False)

    # ---- blog (listado con buscador y filtros) ----
    chips = '<button class="chip f" data-c="" aria-pressed="true">Todas</button>' + "".join(f'<button class="chip f" data-c="{e(k)}" aria-pressed="false">{e(k)}</button>' for k in counts)
    tools = f'<div class="tools"><input id="buscar" type="search" placeholder="Buscar en el blog…  ( / )" aria-label="Buscar en el blog">{chips}</div>' if posts else ""
    grid = f'<div class="grid{" list" if blog_tpl == "lista" else ""}">' + "".join(card(p) for p in posts) + '</div>' if posts else empty
    bhero = f'<div class="hero-in"><div class="box"><span class="kicker">{plural(n, "entrada publicada", "entradas publicadas")}</span><h1>El blog</h1></div></div>'
    files["blog/index.html"] = page("Blog", bhero, f'<div class="sec"><h2>Todas las entradas</h2></div>{tools}{grid}', "blog")

    for g in others:
        ghero = f'<div class="hero-in"><div class="box"><span class="kicker">página</span><h1>{e(g["title"])}</h1></div></div>'
        body_html, toc = render_article(g.get("content") or "")
        files[f"{g['slug']}/index.html"] = page(g["title"], ghero, f'<article class="editorial-post"><div class="prose">{body_html}</div></article>', g["slug"], extra=toc_fab(toc))
    for p in posts:
        mins = max(1, math.ceil(len(p["body"].split()) / 200))
        label = cat.get(p["category_id"], "") or "Entrada"
        tags = "".join(f'<span class="chip">#{e(t)}</span> ' for t in p.get("tags") or [])
        more = [q for q in posts if q is not p][:3]
        more_html = ('<section class="more-reading" aria-label="Seguir leyendo"><h2>Seguir leyendo</h2><div class="grid">' + "".join(card(q) for q in more) + '</div></section>') if more else ""
        body_html, toc = render_article(p["body"])
        phero = f'<div class="hero-in"><div class="box"><span class="kicker">{e(label)} · {e(p["published_at"][:10])} · {mins} min</span><h1>{e(p["title"])}</h1></div></div>'
        cover = f'<figure class="wide cover"><img src="{e(p["cover"])}" alt="" loading="lazy"></figure>' if p.get("cover") and re.match(r"^(https?://|/)[^\s\"'<>]+$", p["cover"]) else ""
        files[f"posts/{p['slug']}/index.html"] = page(p["title"], phero, f'<article class="editorial-post"><a class="more back" href="{base}/blog/">← Todas las entradas</a>{cover}'
                                                      f'<div class="prose">{body_html}</div>{f"<p class=tags>{tags}</p>" if tags else ""}{more_html}</article>', "blog", p["slug"], extra=toc_fab(toc))
    files["api/posts.json"] = json.dumps({"items": [{"slug": p["slug"], "title": p["title"], "summary": p["extract"], "category": cat.get(p["category_id"]),
                                                    "tags": p.get("tags") or [], "published_at": p["published_at"], "url": f"{base}/posts/{p['slug']}/"} for p in posts]}, ensure_ascii=False, indent=2)
    return files


def toc_fab(toc: list[dict]) -> str:
    """Índice flotante (botón «☰ Índice» + panel) con los encabezados ## y ###; sólo aparece si hay al menos dos."""
    if len(toc) < 2:
        return ""
    links = "".join(f'<a class="l{t["level"]}" href="#{html.escape(t["id"])}">{html.escape(t["text"])}</a>' for t in toc)
    return (f'<div class="toc-fab"><button type="button" aria-expanded="false" aria-controls="toc-panel">☰ Índice</button>'
            f'<nav id="toc-panel" aria-label="Índice del artículo" hidden><b>En este artículo</b>{links}</nav></div>')


def write_site(files: dict[str, str | bytes], out_dir: str) -> None:
    root = Path(out_dir).resolve()
    for rel, content in files.items():
        target = (root / rel).resolve()
        if root not in target.parents:
            raise BuildError("WRITE_FAILED", f"Ruta fuera de la carpeta de salida: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    for old in root.rglob("*"):                                     # borra lo que ya no existe (p. ej. una entrada archivada)
        if old.is_file() and old.relative_to(root).as_posix() not in files:
            old.unlink()
    for folder in sorted((d for d in root.rglob("*") if d.is_dir()), reverse=True):
        if not any(folder.iterdir()):
            folder.rmdir()
