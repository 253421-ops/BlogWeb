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
