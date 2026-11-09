"""EL GENERADOR: 1) EXTRAER lo publicado del CMS  2) RENDERIZAR todas las páginas en memoria  3) PUBLICAR los archivos.
Si falla algo antes del paso 3, el sitio anterior queda intacto."""
import html
import json
import math
from pathlib import Path

from common.markdown import render_markdown


class BuildError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def from_bundle(bundle: dict):
    """Traduce el contenido que envía el CMS (camelCase) a lo que usa el renderizador."""
    posts = [{"post_id": p["id"], "title": p["title"], "slug": p["slug"], "body": p.get("content") or "", "summary": p.get("excerpt"),
              "category_id": p.get("categoryId"), "status": "PUBLICADO", "published_at": p.get("publishedAt") or p["createdAt"], "tags": []}
             for p in bundle.get("posts", []) if p.get("status") == "published"]
    categories = [{"category_id": c["id"], "name": c["name"]} for c in bundle.get("categories", [])]
    pages = [p for p in bundle.get("pages", []) if p.get("status") == "published"]
    return posts, categories, pages


CSS = """:root{color-scheme:dark}body{margin:0;background:#070810;color:#e8ecf8;font:18px/1.7 Georgia,serif}
main{max-width:720px;margin:0 auto;padding:48px 20px}a{color:#7fa4ff}h1,h2{font-weight:600;line-height:1.2}
.meta{font:12px ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#7f8aa8}
.card{display:block;padding:18px 20px;margin:14px 0;border:1px solid #1c2340;border-radius:14px;background:#0b0e1a;text-decoration:none;color:inherit}
.card:hover{border-color:#2f6bff}.card h2{margin:6px 0}.card p{margin:0;color:#9aa6c6;font-size:16px}"""
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


def render_site(posts: list[dict], categories: list[dict], cfg, pages: list[dict] | None = None) -> dict[str, str]:
    base = cfg.site_base.rstrip("/")
    cat = {c["category_id"]: c["name"] for c in categories}
    posts = sorted((p for p in posts if p.get("status") == "PUBLICADO"), key=lambda p: p.get("published_at", ""), reverse=True)
    e = html.escape

    def page(title: str, body: str, slug: str | None = None) -> str:
        return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{e(title)} · {e(cfg.site_title)}</title><link rel="stylesheet" href="{base}/assets/style.css"></head>'
                f'<body{f" data-slug={chr(34)}{e(slug)}{chr(34)}" if slug else ""}><main>{body}</main>'
                f'<script src="{base}/assets/tracker.js" data-endpoint="{e(cfg.metrics_url)}/api/v1/events" defer></script></body></html>')

    def card(p):
        extract = p.get("summary") or (p["body"][:160] + "…")
        return (f'<a class="card" href="{base}/posts/{e(p["slug"])}/"><span class="meta">{e(cat.get(p["category_id"], ""))} · {e(p["published_at"][:10])}</span>'
                f'<h2>{e(p["title"])}</h2><p>{e(extract)}</p></a>')

    files = {"assets/style.css": CSS, "assets/tracker.js": TRACKER}
    pages = pages or []
    landing = next((g for g in pages if g.get("type") == "landing"), None)
    intro = render_markdown(landing["content"]) if landing and landing.get("content") else f"<p>{e(cfg.site_description)}</p>"
    nav = "".join(f'<a href="{base}/{e(g["slug"])}/">{e(g["title"])}</a> · ' for g in pages if g.get("type") != "landing")
    files["index.html"] = page(cfg.site_title, f'<p class="meta">{nav}Blog</p><h1>{e(cfg.site_title)}</h1>{intro}' + ("".join(card(p) for p in posts) or "<p>Aún no hay entradas publicadas.</p>"))
    for g in pages:
        if g.get("type") != "landing":
            files[f"{g['slug']}/index.html"] = page(g["title"], f'<p class="meta"><a href="{base}/">← Inicio</a></p><h1>{e(g["title"])}</h1>{render_markdown(g.get("content") or "")}')
    for p in posts:
        minutes = max(1, math.ceil(len(p["body"].split()) / 200))
        tags = "".join(f'<span class="meta">#{e(t)} </span>' for t in p.get("tags") or [])
        files[f"posts/{p['slug']}/index.html"] = page(p["title"], f'<p class="meta"><a href="{base}/">← Inicio</a> · {e(cat.get(p["category_id"], ""))} · {e(p["published_at"][:10])} · {minutes} min</p>'
                                                      f'<h1>{e(p["title"])}</h1>{render_markdown(p["body"])}<p>{tags}</p>', p["slug"])
    files["api/posts.json"] = json.dumps({"items": [{"slug": p["slug"], "title": p["title"], "summary": p.get("summary"), "category": cat.get(p["category_id"]),
                                                    "tags": p.get("tags") or [], "published_at": p["published_at"], "url": f"{base}/posts/{p['slug']}/"} for p in posts]}, ensure_ascii=False, indent=2)
    return files


def write_site(files: dict[str, str], out_dir: str) -> None:
    root = Path(out_dir).resolve()
    for rel, content in files.items():
        target = (root / rel).resolve()
        if root not in target.parents:
            raise BuildError("WRITE_FAILED", f"Ruta fuera de la carpeta de salida: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    for old in root.rglob("*"):                                     # borra lo que ya no existe (p. ej. una entrada archivada)
        if old.is_file() and old.relative_to(root).as_posix() not in files:
            old.unlink()
    for folder in sorted((d for d in root.rglob("*") if d.is_dir()), reverse=True):
        if not any(folder.iterdir()):
            folder.rmdir()
