import json

from fastapi.testclient import TestClient

from common.db import make_engine
from common.security import sign_token
from generador.config import Settings
from generador.main import create_app

SECRET = "secreto-de-prueba-0123456789-0123456789"
H = lambda scope, sub="cms": {"Authorization": f"Bearer {sign_token(SECRET, sub, scope)}"}


def test_generador_compila_publica_y_falla_con_gracia(tmp_path):
    bundle = {"blog": {"id": 1, "name": "Sigo intentándolo"},
              "categories": [{"id": 1, "name": "Vocación"}],
              "pages": [{"id": 1, "type": "landing", "slug": "inicio", "title": "Inicio", "content": "Bienvenida **hola**", "status": "published"},
                        {"id": 2, "type": "page", "slug": "sobre-mi", "title": "Sobre mí", "content": "Soy Brisa", "status": "published"}],
              "posts": [{"id": 1, "title": "Sigo intentándolo", "slug": "sigo-intentandolo", "content": "# Hola\n\n<script>x</script> texto", "categoryId": 1,
                         "status": "published", "publishedAt": "2026-10-20T10:00:00Z", "createdAt": "2026-10-20T10:00:00Z", "excerpt": None}]}
    st = Settings(jwt_secret=SECRET, output_dir=str(tmp_path / "site"))
    c = TestClient(create_app(st, make_engine("sqlite://"), sync_builds=True))
    r = c.post("/api/v1/builds", json={"reason": "cms", "bundle": bundle}, headers=H("builds:write"))
    assert r.status_code == 202 and r.json()["status"] == "QUEUED"
    assert c.post("/api/v1/builds", headers=H("builds:read")).status_code == 403
    assert c.post("/api/v1/builds").status_code == 401
    job = c.get("/api/v1/builds/latest", headers=H("builds:read")).json()
    assert job["status"] == "SUCCEEDED" and job["pages_generated"] == 3   # inicio (con «sobre mí» dentro), blog y la entrada
    page = (tmp_path / "site/posts/sigo-intentandolo/index.html").read_text(encoding="utf-8")
    assert "<script>x" not in page and 'data-slug="sigo-intentandolo"' in page and "/api/v1/events" in page   # sin XSS y con el script de visitas
    assert "<strong>hola</strong>" in (tmp_path / "site/index.html").read_text(encoding="utf-8")
    assert "Todas las entradas" in (tmp_path / "site/blog/index.html").read_text(encoding="utf-8")               # página del blog con listado
    assert "<svg" in (tmp_path / "site/index.html").read_text(encoding="utf-8") and "--sky1" in (tmp_path / "site/assets/style.css").read_text(encoding="utf-8")
    assert json.loads((tmp_path / "site/api/posts.json").read_text(encoding="utf-8"))["items"][0]["slug"] == "sigo-intentandolo"
    assert "Sigo intentándolo" in c.get("/site/posts/sigo-intentandolo/").text                                # el servicio sirve el sitio
    bundle["posts"][0]["status"] = "draft"                                                                    # vuelve a borrador en el CMS
    c.post("/api/v1/builds", json={"bundle": bundle}, headers=H("builds:write"))
    assert not (tmp_path / "site/posts/sigo-intentandolo").exists()
    sin = TestClient(create_app(Settings(jwt_secret=SECRET, output_dir=str(tmp_path / "otro" / "site")), make_engine("sqlite://"), sync_builds=True))
    sin.post("/api/v1/builds", json={}, headers=H("builds:write"))
    failed = sin.get("/api/v1/builds/latest", headers=H("builds:read")).json()
    assert failed["status"] == "FAILED" and failed["error_code"] == "NO_CONTENT"


def test_secciones_imagenes_y_reconstruccion(tmp_path):
    import base64
    png = base64.b64encode(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082")).decode()
    mk = lambda i, t, cat, body: {"id": i, "title": t, "slug": f"p{i}", "content": body, "categoryId": cat, "status": "published",
                                  "publishedAt": f"2026-10-2{i}T10:00:00Z", "createdAt": "2026-10-20T10:00:00Z", "excerpt": None}
    bundle = {"blog": {"id": 1, "name": "Sigo"}, "media": [{"url": "/uploads/1/abc.png", "name": "abc.png", "data": png}],
              "categories": [{"id": 1, "name": "Dibujos"}, {"id": 2, "name": "Proyectos"}, {"id": 3, "name": "Pensamientos"}, {"id": 4, "name": "Innovación textil"}, {"id": 5, "name": "Vocación"}],
              "pages": [{"id": 1, "type": "page", "slug": "sobre-mi", "title": "Sobre mí", "content": "![yo](/uploads/1/abc.png)\n\nSoy **Brisa**", "status": "published"}],
              "posts": [mk(1, "Mi gato", 1, "![gato](https://cms.x/uploads/1/abc.png)"), mk(2, "Alkemon", 2, "juego"), mk(3, "Pienso", 3, "algo"),
                        mk(4, "Tinte natural", 4, "texto"), mk(5, "Mi primer post", 5, "hola")]}
    db = f"sqlite:///{tmp_path / 'g.db'}"
    st = Settings(jwt_secret=SECRET, output_dir=str(tmp_path / "site"), database_url=db)
    c = TestClient(create_app(st, make_engine(db), sync_builds=True))
    c.post("/api/v1/builds", json={"bundle": bundle}, headers=H("builds:write"))
    home = (tmp_path / "site/index.html").read_text(encoding="utf-8")
    for anchor in ("sobre-mi", "dibujos", "carrera", "textil", "proyectos", "materias", "herramientas", "pensamientos", "blog"):
        assert f'id="{anchor}"' in home
    assert "/site/assets/media/abc.png" in home and "<strong>Brisa</strong>" in home          # foto y texto de «sobre-mi»
    assert 'class="frame has"' in home and "Mi gato" in home and "Alkemon" in home and "Tinte natural" in home
    assert home.count("Mi primer post") >= 1 and (tmp_path / "site/assets/media/abc.png").read_bytes()[:4] == b"\x89PNG"
    assert "cms.x" not in (tmp_path / "site/posts/p1/index.html").read_text(encoding="utf-8")   # la URL del CMS se cambia por la local
    # el disco se borra (Render durmió) → al arrancar se reconstruye con lo guardado en la base
    import shutil
    shutil.rmtree(tmp_path / "site")
    create_app(st, make_engine(db), sync_builds=True)
    assert 'id="dibujos"' in (tmp_path / "site/index.html").read_text(encoding="utf-8")


def test_extracto_limpio_sin_markdown_crudo():
    from common.markdown import extract_clean_excerpt
    assert extract_clean_excerpt("![Captura de pantalla 2026-11-04 223856]") == ""                 # imagen cortada a medias
    assert extract_clean_excerpt("![Captura](/uploads/1/x.png)\n\n## Hola **mundo** con [un enlace](http://a.b) y `código`.") == "Hola mundo con un enlace y código."
    largo = extract_clean_excerpt("palabra " * 80, 150)
    assert len(largo) <= 150 and largo.endswith("…")
    assert "```" not in extract_clean_excerpt("antes\n```python\nprint(1)\n```\ndespués") and "[^nota" not in extract_clean_excerpt("a[^nota: x]b")


def test_markdown_editorial_y_seguridad():
    from common.markdown import render_article
    html, toc = render_article("## Uno\n\nTexto[^nota: al margen]\n\n>> Cita\n\n:::tip Truco\nhola\n:::\n\n```python\nx = 1\n```\n\n![pie](/a.png#wide)\n\n### Dos\n\n<script>alert(1)</script> [x](javascript:alert(1))")
    assert 'class="sidenote"' in html and 'class="pullquote"' in html and 'class="callout tip"' in html and "Truco" in html
    assert 'class="codeblock"' in html and ">PYTHON<" in html and "data-copy" in html and 'class="wide"' in html and "<figcaption>pie</figcaption>" in html
    assert [t["id"] for t in toc] == ["uno", "dos"]
    assert "<script>" not in html and 'href="javascript' not in html                                  # sigue sin HTML crudo ni enlaces peligrosos


def test_sitio_editorial_landing_modo_claro_y_tarjetas(tmp_path):
    css = ":root{--bg:#fbf8f1;--text:#1d1b16;--accent:#8f5a00;--font-head:'Lora',Georgia,serif;--text-base:18px;--step-3:35.16px}:root[data-mode=dark]{--bg:#070d2b;--text:#eef1ff}"
    mk = lambda i, t, body, **kw: {"id": i, "title": t, "slug": f"p{i}", "content": body, "categoryId": None, "status": "published",
                                   "publishedAt": f"2026-10-2{i}T10:00:00Z", "createdAt": "2026-10-20T10:00:00Z", "excerpt": None, **kw}
    bundle = {"blog": {"id": 1, "name": "Sigo"}, "theme": {"mode": "light", "scene": "papel", "blog": "tarjetas", "fonts_url": "https://fonts.googleapis.com/css2?family=Lora:wght@600;700&display=swap"},
              "theme_css": css, "pages": [], "categories": [],
              "posts": [mk(1, "Cómo terminamos así?", "![Captura de pantalla 2026-11-04 223856](/uploads/1/x.png)\n\nTexto limpio"),
                        mk(2, "Editorial", "## A\n\nHola[^nota: n]\n\n## B\n\n>> Cita\n\n```sql\nselect 1\n```")]}
    st = Settings(jwt_secret=SECRET, output_dir=str(tmp_path / "site"), landing_url="https://mi-landing.vercel.app")
    c = TestClient(create_app(st, make_engine("sqlite://"), sync_builds=True))
    c.post("/api/v1/builds", json={"bundle": bundle}, headers=H("builds:write"))
    blog = (tmp_path / "site/blog/index.html").read_text(encoding="utf-8")
    assert "Captura de pantalla" not in blog and "![" not in blog and "Texto limpio" in blog       # sin Markdown crudo en las tarjetas
    post = (tmp_path / "site/posts/p2/index.html").read_text(encoding="utf-8")
    assert 'class="editorial-post"' in post and 'data-mode="light"' in post and 'class="toc-fab"' in post and "data-mode-toggle" in post
    assert 'href="https://mi-landing.vercel.app" data-landing' in post and "family=Lora" in post  # logotipo e «Inicio» vuelven a la Landing
    style = (tmp_path / "site/assets/style.css").read_text(encoding="utf-8")
    assert ":root[data-mode=dark]" in style and "grid-template-columns:[full-start]" in style       # dos paletas y rejilla de 3 carriles
    assert "repeat(auto-fit,minmax(210px,1fr))" in style and "clamp(1.15rem,1.4vw,1.4rem)" in style   # tarjeta «Programación» sin desbordarse
    assert "Programación" in (tmp_path / "site/index.html").read_text(encoding="utf-8")
    # una Landing mal escrita no rompe ni inyecta nada
    st2 = Settings(jwt_secret=SECRET, output_dir=str(tmp_path / "s2"), landing_url='javascript:alert(1)')
    c2 = TestClient(create_app(st2, make_engine("sqlite://"), sync_builds=True))
    c2.post("/api/v1/builds", json={"bundle": bundle}, headers=H("builds:write"))
    assert "javascript:alert" not in (tmp_path / "s2/posts/p2/index.html").read_text(encoding="utf-8")
    # CSS del tema con contenido raro → se usa el de respaldo, nunca se copia
    bundle["theme_css"] = ":root{--x:1}body{display:none}"
    c.post("/api/v1/builds", json={"bundle": bundle}, headers=H("builds:write"))
    css2 = (tmp_path / "site/assets/style.css").read_text(encoding="utf-8")
    assert not css2.startswith(":root{--x:1}") and "}body{display:none}" not in css2 and css2.startswith(":root{--bg:#070d2b")
