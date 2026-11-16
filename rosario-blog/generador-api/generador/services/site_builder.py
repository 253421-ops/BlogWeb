"""EL GENERADOR: 1) EXTRAER lo publicado del CMS  2) RENDERIZAR todas las páginas en memoria  3) PUBLICAR los archivos.
Si falla algo antes del paso 3, el sitio anterior queda intacto."""
import html
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from common.markdown import render_markdown
from generador.services.scene import build_scene


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

BASE_VARS = ("--bg:#070d2b;--bg2:#0e1b4d;--sky1:#050a24;--sky2:#10265e;--sky3:#4d86a8;--moon:#f8e7a0;--mtn1:#1d3b52;--mtn2:#11261f;--tree:#0b1c15;--house:#141a33;"
             "--window:#ffd166;--ground1:#1d3b22;--ground2:#0b1d12;--glow:#f5d36b;--accent:#f5c451;--paper:#fbf1d3;--text:#eef1ff;--font-head:'Dancing Script','Segoe Script',cursive;--font-body:'Montserrat',system-ui,sans-serif")
SAFE_VARS = re.compile(r"^:root\{[A-Za-z0-9#,'\-;:. ()]{0,1500}\}$")      # el CSS del tema sólo puede traer variables, nada más

CSS = """*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;min-height:100vh;color:var(--text);font:16px/1.65 var(--font-body);background:var(--bg);padding-bottom:84px}
h1,h2,h3{font-family:var(--font-head);font-weight:700;line-height:1.1;margin:0}a{color:var(--accent)}
.skip{position:absolute;left:-999px;top:8px;background:var(--accent);color:#14193a;padding:8px 14px;border-radius:10px;z-index:99}.skip:focus{left:12px}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:8px}
.tw{animation:tw 4.5s ease-in-out infinite alternate}@keyframes tw{from{opacity:.25}to{opacity:1}}
@media (prefers-reduced-motion:reduce){.tw{animation:none}html{scroll-behavior:auto}*{transition:none!important}}
.wrap{max-width:1140px;margin:0 auto;padding:0 22px}
.scene{position:relative;overflow:hidden;min-height:clamp(560px,86vh,820px);display:flex;flex-direction:column;background:var(--sky1)}
.scene.compact{min-height:300px}.scene.compact .hero-in{padding-top:12px}
.scenesvg{position:absolute;inset:0;width:100%;height:100%}.scene::after{content:"";position:absolute;inset:auto 0 0 0;height:90px;background:linear-gradient(transparent,var(--bg));pointer-events:none}
.top{position:relative;z-index:2;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 0}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:#fff;font:700 28px var(--font-head);text-shadow:0 2px 14px rgba(0,0,0,.45)}.brand svg{width:28px;height:28px}
.kicker{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:600}.top .kicker{text-shadow:0 1px 8px rgba(0,0,0,.6)}
.hero-in{position:relative;z-index:2;flex:1;display:flex;align-items:center;padding-bottom:70px}.hero-in .box{max-width:620px}
.hero-in h1{font-size:clamp(52px,9vw,108px);color:#fff;text-shadow:0 4px 30px rgba(0,0,0,.55);margin:6px 0 12px}.compact .hero-in h1{font-size:clamp(40px,6vw,68px)}
.hero-in .intro{color:#e8eeff;font-size:18px;max-width:52ch;text-shadow:0 2px 14px rgba(0,0,0,.6)}.hero-in .intro p{margin:0 0 10px}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 22px;border-radius:999px;border:1.5px solid var(--accent);color:var(--accent);background:rgba(0,0,0,.25);text-decoration:none;font-weight:600;font-size:14px;transition:transform .15s;backdrop-filter:blur(4px)}
.btn:hover{transform:translateY(-2px)}.btn.fill{background:var(--accent);color:#14193a}
.sec{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:36px 0 16px}.sec h2{font-size:clamp(34px,5vw,48px)}.sec a{font-weight:600;font-size:14px}
.cats{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.cat{padding:20px 22px;border-radius:20px;border:1px solid rgba(255,255,255,.1);background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(255,255,255,.02));text-decoration:none;color:inherit}.cat:hover{border-color:var(--accent)}
.cat h3{font-size:32px}.cat span{color:#aeb9e6;font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}.grid.list{grid-template-columns:1fr}
.card{display:flex;flex-direction:column;gap:8px;padding:20px 22px;border-radius:20px;border:1px solid rgba(255,255,255,.1);background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(255,255,255,.02));text-decoration:none;color:inherit;transition:transform .18s,border-color .18s,box-shadow .18s}
.card:hover,.card:focus-visible{transform:translateY(-4px);border-color:var(--accent);box-shadow:0 14px 34px rgba(0,0,0,.35)}
.card.big{grid-column:span 2;background:linear-gradient(160deg,rgba(255,255,255,.12),rgba(255,255,255,.03))}.card.big h3{font-size:46px}
.grid.list .card{flex-direction:row;align-items:center;flex-wrap:wrap;gap:14px}.grid.list .card h3{flex:1 1 240px}.grid.list .card p{flex:2 1 260px}
.card h3{font-size:32px}.card p{margin:0;color:#c0caee;font-size:15px}.chip{align-self:flex-start;font-size:11px;letter-spacing:.1em;text-transform:uppercase;padding:3px 10px;border-radius:999px;background:rgba(255,255,255,.1);color:var(--accent);font-weight:600;border:0;font-family:inherit}
.meta{font-size:12px;color:#9eaadb;margin-top:auto}.more{color:var(--accent);font-weight:600;font-size:14px}
.note{margin:40px 0 10px;background:var(--paper);color:#2a2540;border-radius:22px;padding:24px 28px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}
.note h2{font-size:36px;color:#241f3d}.note p{margin:4px 0 0;max-width:56ch;font-size:15px}.note .n{font:700 56px var(--font-head);color:#b9780c;line-height:1;text-align:center}
.tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 16px}.tools input{flex:1 1 220px;max-width:340px;padding:10px 16px;border-radius:999px;border:1px solid rgba(255,255,255,.18);background:rgba(0,0,0,.25);color:var(--text);font:inherit}
.chip.f{cursor:pointer;padding:7px 14px;font-size:12px}.chip.f[aria-pressed=true]{background:var(--accent);color:#14193a}
.art{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:34px;padding:26px 0 20px;align-items:start}
.post h1{font-size:clamp(40px,6vw,64px);margin:10px 0 14px}.post .lead{color:#aeb9e6;font-size:13px;display:flex;gap:14px;flex-wrap:wrap;margin-bottom:18px}
.prose{font-size:18px;line-height:1.8;max-width:68ch}.prose h2{font-size:36px;margin:30px 0 8px}.prose h3{font-size:28px;margin:22px 0 6px}.prose p{margin:0 0 16px}
.prose img{max-width:100%;border-radius:16px}.prose blockquote{margin:20px 0;padding:6px 20px;border-left:3px solid var(--accent);color:#d4dcff;font-family:var(--font-head);font-size:26px}
.prose code{background:rgba(255,255,255,.1);padding:2px 6px;border-radius:6px}.prose pre{background:rgba(0,0,0,.35);padding:14px;border-radius:14px;overflow:auto}
aside.side{position:sticky;top:18px;display:grid;gap:14px}.panel{padding:18px 20px;border-radius:18px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.05)}
.panel h3{font-size:28px;margin-bottom:6px}.panel a{display:block;padding:7px 0;color:var(--text);text-decoration:none;border-bottom:1px dashed rgba(255,255,255,.12);font-size:15px}.panel a:last-child{border:0}.panel a:hover{color:var(--accent)}
#prog{position:fixed;z-index:9;top:0;left:0;height:3px;width:0;background:var(--accent)}
.dock{position:fixed;z-index:5;left:50%;bottom:14px;transform:translateX(-50%);display:flex;gap:6px;padding:8px;border-radius:22px;background:rgba(6,10,32,.82);border:1px solid rgba(255,255,255,.14);backdrop-filter:blur(10px);max-width:calc(100vw - 20px);overflow-x:auto}
.dock a{display:flex;align-items:center;gap:7px;padding:10px 16px;border-radius:15px;color:#d4dcff;text-decoration:none;font-size:13px;font-weight:600;white-space:nowrap}
.dock a:hover{background:rgba(255,255,255,.08)}.dock a[aria-current=page]{background:var(--accent);color:#14193a}
.foot{text-align:center;color:#8f9bcb;font-size:12px;padding:26px 0 10px}
@media (max-width:820px){.card.big{grid-column:auto}.art{grid-template-columns:1fr}aside.side{position:static}.top .kicker{display:none}.scene{min-height:560px}}"""

LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M21 3a13 13 0 1 0 8 22A11 11 0 0 1 21 3z" fill="var(--accent)"/></svg>'
SITE_JS = """(function(){var bar=document.getElementById('prog');if(bar){addEventListener('scroll',function(){var d=document.documentElement,m=d.scrollHeight-innerHeight;bar.style.width=(m>0?scrollY/m*100:0)+'%'},{passive:true})}
var q=document.getElementById('buscar'),chips=[].slice.call(document.querySelectorAll('.chip.f')),cards=[].slice.call(document.querySelectorAll('[data-cat]')),cat='';
function apply(){var t=q?q.value.toLowerCase():'';cards.forEach(function(c){var ok=(!cat||c.dataset.cat===cat)&&(!t||c.dataset.t.indexOf(t)>-1);c.style.display=ok?'':'none'})}
chips.forEach(function(b){b.addEventListener('click',function(){cat=b.dataset.c;chips.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});apply()})});if(q)q.addEventListener('input',apply);
document.addEventListener('keydown',function(e){var tg=document.activeElement.tagName;if(/INPUT|TEXTAREA/.test(tg)||e.ctrlKey||e.metaKey||e.altKey)return;
var c=cards.filter(function(x){return x.style.display!=='none'}),i=c.indexOf(document.activeElement);
if(e.key==='j'){e.preventDefault();(c[i+1]||c[0])&&(c[i+1]||c[0]).focus()}else if(e.key==='k'){e.preventDefault();(c[i-1]||c[c.length-1])&&(c[i-1]||c[c.length-1]).focus()}
else if(e.key==='/'&&q){e.preventDefault();q.focus()}else if(e.key==='h'){location.href=document.querySelector('.brand').href}})})();"""

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


@lru_cache(maxsize=1)
def _scene() -> str:
    return build_scene()


def render_site(posts: list[dict], categories: list[dict], cfg, pages: list[dict] | None = None, bundle: dict | None = None) -> dict[str, str]:
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
    tcss = bundle.get("theme_css") or ""
    tcss = tcss if SAFE_VARS.match(tcss) else ":root{" + BASE_VARS + "}"
    pages = pages or []
    others = [g for g in pages if g.get("type") != "landing"]
    n = len(posts)
    plural = lambda k, one, many: f"{k} {one if k == 1 else many}"

    def dock(active: str) -> str:
        items = [("inicio", f"{base}/", "✦ Inicio"), ("blog", f"{base}/blog/", "✎ Blog")] + [(g["slug"], f"{base}/{g['slug']}/", e(g["title"])) for g in others]
        return '<nav class="dock" aria-label="Principal">' + "".join(f'<a href="{h}"{" aria-current=page" if k == active else ""}>{t}</a>' for k, h, t in items) + "</nav>"

    def scene_block(inner: str, compact: bool) -> str:
        return (f'<section class="scene{" compact" if compact else ""}">{_scene()}<div class="wrap" style="position:relative;z-index:2;display:flex;flex-direction:column;flex:1;width:100%">'
                f'<header class="top"><a class="brand" href="{base}/">{LOGO}{e(title)}</a><span class="kicker">{e(desc)[:60]}</span></header>{inner}</div></section>')

    def page(ttl: str, hero: str, body: str, active: str, slug: str | None = None, compact: bool = True) -> str:
        return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{e(ttl)} · {e(title)}</title><meta name="description" content="{e(desc)}">'
                f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                f'<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Montserrat:wght@400;600&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">'
                f'<link rel="stylesheet" href="{base}/assets/style.css"></head>'
                f'<body{f" data-slug={chr(34)}{e(slug)}{chr(34)}" if slug else ""}><a class="skip" href="#contenido">Saltar al contenido</a><div id="prog"></div>'
                f'{scene_block(hero, compact)}<main id="contenido" class="wrap">{body}<footer class="foot">{e(title)} · hecho con un CMS API-First</footer></main>{dock(active)}'
                f'<script src="{base}/assets/site.js" defer></script>'
                f'<script src="{base}/assets/tracker.js" data-endpoint="{e(cfg.metrics_url)}/api/v1/events" defer></script></body></html>')

    def card(p, big=False):
        extract = p.get("summary") or (p["body"][:150] + "…")
        label = cat.get(p["category_id"], "") or "Entrada"
        mins = max(1, math.ceil(len(p["body"].split()) / 200))
        return (f'<a class="card{" big" if big else ""}" href="{base}/posts/{e(p["slug"])}/" data-cat="{e(label)}" data-t="{e((p["title"] + " " + extract).lower())}"><span class="chip">{e(label)}</span>'
                f'<h3>{e(p["title"])}</h3><p>{e(extract)}</p><span class="meta">{e(p["published_at"][:10])} · {mins} min de lectura</span><span class="more">Leer →</span></a>')

    files = {"assets/style.css": tcss + "\n" + CSS, "assets/tracker.js": TRACKER, "assets/site.js": SITE_JS}
    landing = next((g for g in pages if g.get("type") == "landing"), None)
    intro = render_markdown(landing["content"]) if landing and landing.get("content") else f"<p>{e(desc)}</p>"
    empty = '<p class="panel">Aún no hay entradas publicadas. Cuando publiques la primera, aparecerá aquí.</p>'

    # ---- portada ----
    hero = (f'<div class="hero-in"><div class="box"><span class="kicker">un diario de pequeños intentos</span><h1>{e(title)}</h1><div class="intro">{intro}</div>'
            f'<div class="btns"><a class="btn fill" href="{base}/blog/">Leer el blog →</a>' + (f'<a class="btn" href="{base}/{e(others[0]["slug"])}/">{e(others[0]["title"])}</a>' if others else "") + '</div></div></div>')
    counts: dict[str, int] = {}
    for p in posts:
        counts[cat.get(p["category_id"], "") or "Entrada"] = counts.get(cat.get(p["category_id"], "") or "Entrada", 0) + 1
    cats_html = ('<div class="sec"><h2>Lo que encontrarás</h2></div><div class="cats">' + "".join(
        f'<a class="cat" href="{base}/blog/"><h3>{e(k)}</h3><span>{plural(v, "entrada", "entradas")}</span></a>' for k, v in list(counts.items())[:6]) + '</div>') if counts else ""
    latest = ('<div class="sec"><h2>Últimas entradas</h2><a href="' + base + '/blog/">Ver todas →</a></div><div class="grid">' + "".join(card(p) for p in posts[:3]) + '</div>') if posts else '<div class="sec"><h2>Últimas entradas</h2></div>' + empty
    note = (f'<section class="note"><div><h2>Lo importante se cuida despacio</h2><p>Cada entrada es un pequeño paso. No hace falta tenerlo todo claro para empezar a escribir.</p></div>'
            f'<div class="n">{n}<span style="font:600 14px var(--font-body);display:block;color:#6a5a2b">{"entrada" if n == 1 else "entradas"}</span></div></section>')
    files["index.html"] = page(title, hero, cats_html + latest + note, "inicio", compact=False)

    # ---- blog (listado con buscador y filtros) ----
    chips = '<button class="chip f" data-c="" aria-pressed="true">Todas</button>' + "".join(f'<button class="chip f" data-c="{e(k)}" aria-pressed="false">{e(k)}</button>' for k in counts)
    tools = f'<div class="tools"><input id="buscar" type="search" placeholder="Buscar en el blog…  ( / )" aria-label="Buscar en el blog">{chips}</div>' if posts else ""
    grid = f'<div class="grid{" list" if blog_tpl == "lista" else ""}">' + "".join(card(p) for p in posts) + '</div>' if posts else empty
    bhero = f'<div class="hero-in"><div class="box"><span class="kicker">{plural(n, "entrada publicada", "entradas publicadas")}</span><h1>El blog</h1></div></div>'
    files["blog/index.html"] = page("Blog", bhero, f'<div class="sec"><h2>Todas las entradas</h2></div>{tools}{grid}', "blog")

    for g in others:
        ghero = f'<div class="hero-in"><div class="box"><span class="kicker">página</span><h1>{e(g["title"])}</h1></div></div>'
        files[f"{g['slug']}/index.html"] = page(g["title"], ghero, f'<article class="post" style="padding:26px 0"><div class="prose">{render_markdown(g.get("content") or "")}</div></article>', g["slug"])
    for p in posts:
        mins = max(1, math.ceil(len(p["body"].split()) / 200))
        label = cat.get(p["category_id"], "") or "Entrada"
        tags = "".join(f'<span class="chip">#{e(t)}</span> ' for t in p.get("tags") or [])
        more = [q for q in posts if q is not p][:4]
        side = (f'<aside class="side"><div class="panel"><h3>Sobre este blog</h3><p style="margin:0;font-size:14px;color:#b8c2ea">{e(desc)}</p></div>'
                + (f'<div class="panel"><h3>Seguir leyendo</h3>' + "".join(f'<a href="{base}/posts/{e(q["slug"])}/">{e(q["title"])}</a>' for q in more) + '</div>' if more else "") + '</aside>')
        phero = f'<div class="hero-in"><div class="box"><span class="kicker">{e(label)} · {e(p["published_at"][:10])} · {mins} min</span><h1>{e(p["title"])}</h1></div></div>'
        files[f"posts/{p['slug']}/index.html"] = page(p["title"], phero, f'<div class="art"><article class="post"><a class="more" href="{base}/blog/">← Todas las entradas</a>'
                                                      f'<div class="prose" style="margin-top:16px">{render_markdown(p["body"])}</div><p>{tags}</p></article>{side}</div>', "blog", p["slug"])
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
