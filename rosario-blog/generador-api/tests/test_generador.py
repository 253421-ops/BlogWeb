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
    assert job["status"] == "SUCCEEDED" and job["pages_generated"] == 3
    page = (tmp_path / "site/posts/sigo-intentandolo/index.html").read_text(encoding="utf-8")
    assert "<script>x" not in page and 'data-slug="sigo-intentandolo"' in page and "/api/v1/events" in page   # sin XSS y con el script de visitas
    assert "<strong>hola</strong>" in (tmp_path / "site/index.html").read_text(encoding="utf-8")
    assert json.loads((tmp_path / "site/api/posts.json").read_text(encoding="utf-8"))["items"][0]["slug"] == "sigo-intentandolo"
    assert "Sigo intentándolo" in c.get("/site/posts/sigo-intentandolo/").text                                # el servicio sirve el sitio
    bundle["posts"][0]["status"] = "draft"                                                                    # vuelve a borrador en el CMS
    c.post("/api/v1/builds", json={"bundle": bundle}, headers=H("builds:write"))
    assert not (tmp_path / "site/posts/sigo-intentandolo").exists()
    sin = TestClient(create_app(Settings(jwt_secret=SECRET, output_dir=str(tmp_path / "otro" / "site")), make_engine("sqlite://"), sync_builds=True))
    sin.post("/api/v1/builds", json={}, headers=H("builds:write"))
    failed = sin.get("/api/v1/builds/latest", headers=H("builds:read")).json()
    assert failed["status"] == "FAILED" and failed["error_code"] == "NO_CONTENT"
