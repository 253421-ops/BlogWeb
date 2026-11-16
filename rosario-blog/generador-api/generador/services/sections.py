"""Secciones de la portada: sobre mí, dibujos, carrera, textil y ambiente, proyectos, materias, herramientas, pensamientos y blog.
Lo que Brisa escribe en el CMS (entradas por categoría y la página «sobre-mi») manda; si no hay nada, se muestran textos de ejemplo."""
import html
import re
import unicodedata

e = html.escape

AREAS = [("Programación", "Escribir instrucciones para que las ideas cobren vida"), ("Redes", "Cómo se comunican los equipos y los servicios"),
         ("Base de datos", "Guardar y encontrar información con orden"), ("Interfaces", "Lo que se ve y se toca: el diseño y el código se abrazan"),
         ("Análisis y lógica", "Dividir un problema grande en pasos pequeños")]
MATERIAS = [("Programación", "Mi primer idioma con la computadora."), ("Bases de datos", "Cómo guardar todo con orden."), ("Redes", "Cómo viajan los datos."),
            ("Estructuras de datos", "Ordenar para encontrar rápido."), ("Desarrollo web", "HTML, CSS y JavaScript en acción."), ("Matemáticas", "La lógica detrás de todo."),
            ("Inglés", "La puerta a la documentación."), ("Innovación", "Convertir ideas en proyectos.")]
PROYECTOS = ["LoveSong", "Juego de Trivia", "Real Social UI", "Calculadora Prueba 2", "Leveling Pages", "Alkemon", "CleanData"]
PENSAMIENTOS = ["Tal vez crear y programar no sean mundos tan diferentes.", "No hace falta ser la programadora de sótano para pertenecer.",
                "Lo importante no es entenderlo todo hoy, sino seguir intentándolo."]
TEXTIL = [("Menos desperdicio", "Datos para cortar y producir justo lo necesario."), ("Menos agua", "Procesos y tintes que cuidan los ríos."),
          ("Materiales nuevos", "Fibras y trazabilidad para saber de dónde viene cada prenda.")]
TOOLS = [("Java", "Jv", "#f89820", "Lenguaje", "Lenguaje orientado a objetos muy usado en aplicaciones empresariales y en Android."),
         ("Python", "Py", "#4b8bbe", "Lenguaje", "Lenguaje claro y versátil: datos, inteligencia artificial, automatización y APIs con FastAPI."),
         ("C", "C", "#5c8dd6", "Lenguaje", "Lenguaje cercano al hardware; la base de muchos sistemas y de lo que viene después."),
         ("C++", "C++", "#00a3e0", "Lenguaje", "C con objetos: rendimiento para videojuegos, sistemas y software exigente."),
         ("JavaScript", "JS", "#f7df1e", "Lenguaje", "El lenguaje que le da vida e interacción a las páginas web."),
         ("SQL", "SQL", "#66d9a8", "Lenguaje", "Lenguaje para consultar y administrar bases de datos."),
         ("HTML", "&lt;/&gt;", "#e44d26", "Herramienta", "La estructura de una página web: títulos, textos, imágenes y enlaces."),
         ("CSS", "{ }", "#2965f1", "Herramienta", "El estilo: colores, tipografías, animaciones y todo lo que hace bonita una página."),
         ("GitHub", "GH", "#c9d1d9", "Herramienta", "Guarda el código con Git, conserva su historia y permite colaborar."),
         ("Claude", "Cl", "#d97757", "IA", "Asistente de inteligencia artificial que me ayuda a aprender y a construir."),
         ("IA", "IA", "#b388ff", "Concepto", "Sistemas que aprenden de datos. Una herramienta de apoyo, no un reemplazo de pensar."),
         ("ChatGPT", "GPT", "#74aa9c", "IA", "Asistente conversacional de IA para resolver dudas y explorar ideas."),
         ("Cisco", "Cs", "#049fd9", "Redes", "Equipos y formación en redes para entender cómo viajan los datos.")]

# nombre de categoría (sin acentos, minúsculas) -> sección. Se busca "contiene".
KEYS = {"dibujo": "dibujos", "proyecto": "proyectos", "pensamiento": "pensamientos", "textil": "textil", "ambiente": "textil"}
SPECIAL = set(KEYS.values())
IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def section_of(category_name: str) -> str | None:
    n = norm(category_name or "")
    return next((v for k, v in KEYS.items() if k in n), None)


def cover(body: str) -> str | None:
    m = IMG.search(body or "")
    return m.group(1) if m else None


def split_posts(posts: list[dict], cat: dict) -> tuple[dict[str, list[dict]], list[dict]]:
    """(entradas por sección especial, entradas «normales» del blog)."""
    special: dict[str, list[dict]] = {k: [] for k in SPECIAL}
    normal = []
    for p in posts:
        s = section_of(cat.get(p["category_id"], ""))
        (special[s] if s else normal).append(p)
    return special, normal


def head(id_: str, title: str, sub: str = "", link: str = "") -> str:
    return (f'<div class="sec" id="{id_}"><div><h2>{title}</h2>' + (f'<p class="sub">{sub}</p>' if sub else "") + "</div>" + (link or "") + "</div>")


def render_sections(base: str, special: dict, normal: list, about_html: str | None, about_img: str | None, card, empty: str, n_total: int) -> str:
    out: list[str] = []

    # ---- sobre mí ----
    photo = (f'<div class="photo has" style="background-image:url({e(about_img)})" role="img" aria-label="Foto de Brisa"></div>' if about_img
             else '<div class="photo"><span>Tu foto aquí<small>sube una imagen en la página «sobre-mi»</small></span></div>')
    text = about_html or ("<h3>Hola, soy Brisa</h3><p>Estudio Ingeniería en TI e Innovación Digital (4.º cuatrimestre). Dibujo, me apasiona el diseño de ropa, investigar, "
                          "inventar historias y admirar la naturaleza. Amo los autos, el violín y leer. No siempre entiendo todo… pero sigo intentándolo.</p>")
    chips = "".join(f"<span class='chip'>{c}</span>" for c in ("Dibujo", "Moda", "Lectura", "Autos", "Violín", "Plantas"))
    out.append(head("sobre-mi", "¿Quién soy?") + f'<div class="about">{photo}<article class="card about-t"><div class="prose">{text}</div><p class="chips">{chips}</p></article></div>'
               '<h3 class="mini">Nos encontramos en el camino</h3><div class="links"><a class="card" href="#">Instagram <small>@tu_usuario</small></a>'
               '<a class="card" href="#">WhatsApp <small>escríbeme</small></a><a class="card" href="#">GitHub <small>mi código</small></a></div>')

    # ---- dibujos ----
    def frame(p):
        img = cover(p["body"])
        style = f' style="background-image:url({e(img)})"' if img else ""
        return (f'<a class="frame{" has" if img else ""}"{style} href="{base}/posts/{e(p["slug"])}/" aria-label="{e(p["title"])}"><span class="cap">{e(p["title"])}</span></a>')
    dr = special["dibujos"]
    frames = "".join(frame(p) for p in dr) + "".join('<div class="frame ghost"><span>Tu dibujo</span></div>' for _ in range(max(0, 6 - len(dr))))
    out.append(head("dibujos", "Mis dibujos", "Cada marco es una entrada de la categoría «Dibujos»: pon una imagen y aparece aquí.") + f'<div class="gallery">{frames}</div>')

    # ---- carrera ----
    areas = "".join(f'<article class="card"><h3>{e(a)}</h3><p>{e(b)}</p></article>' for a, b in AREAS)
    out.append(head("carrera", "¿Qué se estudia en software?", "Un recorrido honesto, sin tecnicismos.") + f'<div class="grid five">{areas}</div>'
               '<div class="banner"><b>Puede ser para ti si…</b><span>Te gusta crear y probar ideas</span><span>Disfrutas resolver retos</span><span>Tienes curiosidad por entender</span></div>')

    # ---- innovación textil y ambiente ----
    tx = "".join(f'<article class="card"><h3>{e(a)}</h3><p>{e(b)}</p></article>' for a, b in TEXTIL)
    tposts = special["textil"]
    out.append(head("textil", "Innovación textil y ambiente", "Mi razón de fondo: que la tecnología ayude a que la moda contamine menos.") + f'<div class="grid">{tx}</div>'
               + (f'<div class="grid" style="margin-top:16px">{"".join(card(p) for p in tposts)}</div>' if tposts else ""))

    # ---- proyectos ----
    pj = special["proyectos"]
    stars = ("".join(f'<a class="card star" href="{base}/posts/{e(p["slug"])}/"><span class="chip">Proyecto</span><h3>{e(p["title"])}</h3><p>{e(p.get("summary") or p["body"][:120])}</p><span class="more">Ver →</span></a>' for p in pj)
             if pj else "".join(f'<div class="card star"><span class="chip">Proyecto</span><h3>{e(n)}</h3><p>Una estrella más de mi constelación.</p></div>' for n in PROYECTOS))
    out.append(head("proyectos", "Proyectos en mi constelación", "Cada proyecto es una estrella. Se llenan con entradas de la categoría «Proyectos».") + f'<div class="grid">{stars}</div>')

    # ---- materias ----
    out.append(head("materias", "Mis materias", "Lo que estoy aprendiendo este cuatrimestre.") + '<div class="grid four">'
               + "".join(f'<article class="card"><h3>{e(a)}</h3><p>{e(b)}</p></article>' for a, b in MATERIAS) + "</div>")

    # ---- herramientas (cinta de película) ----
    reel = "".join(f'<button class="fr" data-i="{i % len(TOOLS)}" style="--c:{t[2]}" aria-label="{e(t[0])}"><b>{t[1]}</b><small>{e(t[0])}</small></button>' for i, t in enumerate(TOOLS + TOOLS))
    info = "".join(f'<template data-i="{i}"><h3>{e(t[0])} <small>{e(t[3])}</small></h3><p>{e(t[4])}</p></template>' for i, t in enumerate(TOOLS))
    out.append(head("herramientas", "Herramientas y lenguajes", "Pasa el cursor para detener la cinta y toca un fotograma.")
               + f'<div class="film"><div class="reel">{reel}</div></div><article class="card" id="info" aria-live="polite"><h3>Elige un fotograma</h3><p>Aquí te cuento en qué consiste cada uno.</p></article>{info}')

    # ---- pensamientos ----
    ps = special["pensamientos"]
    quotes = ("".join(f'<a class="quote" href="{base}/posts/{e(p["slug"])}/"><q>{e(p.get("summary") or p["body"][:160])}</q><span>{e(p["title"])}</span></a>' for p in ps)
              if ps else "".join(f'<blockquote class="quote"><q>{e(t)}</q></blockquote>' for t in PENSAMIENTOS))
    out.append(head("pensamientos", "Pensamientos", "Lo que pienso… y lo que tú quieras dejarme.") + f'<div class="grid">{quotes}</div>'
               '<form id="cmf" class="card"><label>Tu nombre<input id="cn" maxlength="40" placeholder="Anónimo"></label>'
               '<label>Tu pensamiento<textarea id="ct" maxlength="280" rows="2" placeholder="Deja un pensamiento…"></textarea></label>'
               '<button class="btn fill">Dejar pensamiento ✦</button><small class="meta">Se guarda sólo en tu navegador.</small></form><div class="grid" id="cm"></div>')

    # ---- el blog ----
    latest = f'<div class="grid">{"".join(card(p) for p in normal[:3])}</div>' if normal else empty
    link = f'<a class="more" href="{base}/blog/">Ver todas ({n_total}) →</a>'
    out.append(head("blog", "El blog", "Lo que escribo desde el CMS aparece aquí al publicar.", link) + latest)
    return "\n".join(f"<section class=\"block\">{x}</section>" for x in out)


CSS = """
.block{padding-top:26px;scroll-margin-top:12px}.block .sec{margin:20px 0 14px}.sub{margin:6px 0 0;color:#aeb9e6;font-size:15px}.mini{font-size:30px;margin:22px 0 10px}
.about{display:grid;grid-template-columns:minmax(220px,300px) 1fr;gap:18px}.photo{min-height:300px;border-radius:24px;border:2px dashed rgba(255,255,255,.25);display:grid;place-items:center;text-align:center;color:#aeb9e6;background:rgba(255,255,255,.04) center/cover}
.photo small{display:block;font-size:12px;margin-top:6px}.photo.has{border:0;box-shadow:0 14px 40px rgba(0,0,0,.4)}.photo.has span{display:none}
.about-t .prose{font-size:17px}.about-t .prose h3{font-size:36px;margin:0 0 6px}.chips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 0}
.links{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}.links small{color:#9eaadb}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:16px}
.frame{position:relative;aspect-ratio:4/5;border-radius:6px;border:10px solid #f3e6c4;box-shadow:0 12px 30px rgba(0,0,0,.45),inset 0 0 0 2px rgba(0,0,0,.25);background:rgba(255,255,255,.05) center/cover;display:grid;place-items:center;color:#8f9bcb;text-decoration:none;transition:transform .2s}
.frame.has:hover,.frame.has:focus-visible{transform:rotate(-1.2deg) translateY(-4px)}.frame.ghost{border-style:dashed;border-color:rgba(243,230,196,.35);box-shadow:none}
.frame .cap{position:absolute;inset:auto 0 0 0;padding:26px 12px 10px;background:linear-gradient(transparent,rgba(0,0,0,.75));color:#fff;font:700 24px var(--font-head)}
.grid.five{grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}.grid.four{grid-template-columns:repeat(auto-fill,minmax(210px,1fr))}
.banner{margin-top:16px;padding:18px 22px;border-radius:20px;background:var(--paper);color:#2a2540;display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center}.banner b{font:700 32px var(--font-head);margin-right:6px}.banner span{padding:6px 12px;border-radius:999px;background:rgba(0,0,0,.07);font-size:14px}
.card.star{position:relative;overflow:hidden}.card.star::after{content:"✦";position:absolute;right:16px;top:12px;color:var(--accent);opacity:.7}
.film{overflow:hidden;border-radius:16px;background:#0a0a0f;border:1px solid rgba(255,255,255,.12);padding:14px 0;margin-bottom:14px;-webkit-mask:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent);mask:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent)}
.reel{display:flex;gap:12px;width:max-content;animation:reel 60s linear infinite}.film:hover .reel,.film:focus-within .reel{animation-play-state:paused}@keyframes reel{to{transform:translateX(-50%)}}
.fr{flex:none;width:96px;height:112px;border-radius:10px;border:2px solid var(--c);background:rgba(255,255,255,.04);color:var(--c);cursor:pointer;display:grid;place-content:center;gap:4px;font:inherit}.fr b{font-size:26px}.fr small{color:#cfd6f5;font-size:11px}
.fr.sel{background:var(--c);color:#111}.fr.sel small{color:#111}#info small{font:600 12px var(--font-body);color:var(--accent);margin-left:6px}
.quote{margin:0;padding:22px 24px;border-radius:20px;border-left:4px solid var(--accent);background:rgba(255,255,255,.05);color:inherit;text-decoration:none;display:flex;flex-direction:column;gap:8px}
.quote q{font:600 28px/1.2 var(--font-head);quotes:"“" "”"}.quote span{font-size:12px;color:#9eaadb}
#cmf{margin:16px 0;gap:12px}#cmf label{display:grid;gap:4px;font-size:13px;color:#aeb9e6}#cmf input,#cmf textarea{padding:10px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.18);background:rgba(0,0,0,.25);color:var(--text);font:inherit}
#cmf .btn{align-self:flex-start;cursor:pointer}
.dock a.on{background:var(--accent);color:#14193a}.dock{scrollbar-width:none}
@media (max-width:820px){.about{grid-template-columns:1fr}.photo{min-height:220px}}
@media (prefers-reduced-motion:reduce){.reel{animation:none}}
"""

JS = """(function(){var r=document.querySelector('.reel');if(!r)return;var info=document.getElementById('info');
r.addEventListener('click',function(ev){var f=ev.target.closest('.fr');if(!f)return;var t=document.querySelector('template[data-i="'+f.dataset.i+'"]');if(!t)return;
document.querySelectorAll('.fr').forEach(function(x){x.classList.toggle('sel',x.dataset.i===f.dataset.i)});info.innerHTML=t.innerHTML});
var ids=[].map.call(document.querySelectorAll('.dock a[href^="#"]'),function(a){return a.getAttribute('href').slice(1)});
if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){document.querySelectorAll('.dock a').forEach(function(a){var on=a.getAttribute('href')==='#'+en.target.id;a.classList.toggle('on',on);if(on&&a.scrollIntoView)a.scrollIntoView({inline:'center',block:'nearest'})})}})},{rootMargin:'-30% 0px -60% 0px'});
ids.forEach(function(i){var el=document.getElementById(i);if(el)io.observe(el)})}
var KEY='brisa:cm',cm=[];try{cm=JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){}
var box=document.getElementById('cm'),f=document.getElementById('cmf');
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return '&#'+c.charCodeAt(0)+';'})}
function draw(){if(box)box.innerHTML=cm.map(function(c){return '<article class="card"><h3>'+esc(c.n)+'</h3><p>'+esc(c.t)+'</p></article>'}).join('')}
if(f){f.addEventListener('submit',function(ev){ev.preventDefault();var t=document.getElementById('ct').value.trim().slice(0,280);if(!t)return;
cm.unshift({n:document.getElementById('cn').value.trim().slice(0,40)||'Anónimo',t:t});try{localStorage.setItem(KEY,JSON.stringify(cm.slice(0,50)))}catch(e){}document.getElementById('ct').value='';draw()});draw()}})();"""
