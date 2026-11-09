import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "secreto123"
os.environ["SECRET_KEY"] = "clave-de-pruebas-de-al-menos-32-caracteres"
os.environ["BUILDER_URL"] = ""
os.environ["METRICS_URL"] = ""

import pytest
from fastapi.testclient import TestClient

from app.main import app

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
       b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe"
       b"\xa7\x1b\xa5\xa4\x00\x00\x00\x00IEND\xaeB`\x82")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "secreto123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}


def test_requires_auth(client):
    assert client.get("/api/blogs").status_code == 401
    bad = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "mal"})
    assert bad.status_code == 401


def test_full_flow(client, auth):
    assert client.get("/api/auth/me", headers=auth).json()["email"] == "admin@example.com"

    blog = client.post("/api/blogs", json={"name": "Mi Blog Ñandú"}, headers=auth)
    assert blog.status_code == 201
    b = blog.json()
    assert b["slug"] == "mi-blog-nandu"
    base = f"/api/blogs/{b['id']}"

    # páginas: solo una landing
    land = client.post(f"{base}/pages", json={"title": "Inicio", "type": "landing", "status": "published"}, headers=auth)
    assert land.status_code == 201 and land.json()["slug"] == "inicio"
    dup = client.post(f"{base}/pages", json={"title": "Otra", "type": "landing"}, headers=auth)
    assert dup.status_code == 409
    about = client.post(f"{base}/pages", json={"title": "Acerca de", "status": "published"}, headers=auth)
    assert about.status_code == 201
    pid = about.json()["id"]
    assert client.put(f"{base}/pages/{pid}", json={"title": "Sobre mí", "content": "Hola", "status": "published"}, headers=auth).json()["content"] == "Hola"
    assert len(client.get(f"{base}/pages", headers=auth).json()) == 2

    # categorías y publicaciones
    cat = client.post(f"{base}/categories", json={"name": "Tecnología"}, headers=auth).json()
    assert cat["slug"] == "tecnologia"
    post = client.post(f"{base}/posts", json={"title": "Primer post", "content": "# Hola", "categoryId": cat["id"]}, headers=auth)
    assert post.status_code == 201 and post.json()["status"] == "draft"
    post_id = post.json()["id"]
    bad_cat = client.post(f"{base}/posts", json={"title": "X", "categoryId": 9999}, headers=auth)
    assert bad_cat.status_code == 422
    same = client.post(f"{base}/posts", json={"title": "Primer post"}, headers=auth).json()
    assert same["slug"] == "primer-post-2"

    pub = client.patch(f"{base}/posts/{post_id}/status", json={"status": "published"}, headers=auth).json()
    assert pub["status"] == "published" and pub["publishedAt"]

    lst = client.get(f"{base}/posts", params={"status": "published", "categoryId": cat["id"]}, headers=auth).json()
    assert lst["total"] == 1 and "content" not in lst["items"][0]
    assert client.get(f"{base}/posts/{post_id}", headers=auth).json()["content"] == "# Hola"

    # imágenes
    up = client.post(f"{base}/media", files={"file": ("a.png", PNG, "image/png")}, headers=auth)
    assert up.status_code == 201
    m = up.json()
    assert client.get(m["url"]).status_code == 200
    assert client.post(f"{base}/media", files={"file": ("a.txt", b"hola", "text/plain")}, headers=auth).status_code == 415
    assert client.delete(f"{base}/media/{m['id']}", headers=auth).status_code == 204

    # build (simulado) + preview
    assert client.get(f"{base}/preview", headers=auth).status_code == 404
    build = client.post("/api/build", json={"blogId": b["id"]}, headers=auth)
    assert build.status_code == 201
    bj = build.json()
    assert bj["status"] == "success" and bj["result"]["posts"] == 1 and bj["result"]["pages"] == 2
    assert client.get(f"/api/builds/{bj['id']}", headers=auth).json()["status"] == "success"
    assert client.get(f"{base}/preview", headers=auth).json()["id"] == bj["id"]

    # métricas (simuladas)
    met = client.get(f"{base}/metrics", headers=auth).json()
    assert met == {"visitas": 0, "visitantesUnicos": 0, "simulated": True}

    # borrados
    assert client.delete(f"{base}/categories/{cat['id']}", headers=auth).status_code == 204
    assert client.get(f"{base}/posts/{post_id}", headers=auth).json()["categoryId"] is None
    assert client.delete(f"{base}/posts/{post_id}", headers=auth).status_code == 204
    assert client.delete(base, headers=auth).status_code == 204
    assert client.get(base, headers=auth).status_code == 404


def test_builder_integration_and_failure(client, auth):
    from app.dependencies import get_builder_client

    class FakeBuilder:
        def __init__(self, fail=False):
            self.fail, self.received = fail, None

        def build(self, bundle):
            if self.fail:
                raise RuntimeError("Builder caído")
            self.received = bundle
            return {"files": ["index.html"]}

    b = client.post("/api/blogs", json={"name": "Blog Builder"}, headers=auth).json()
    base = f"/api/blogs/{b['id']}"
    client.post(f"{base}/posts", json={"title": "Visible", "status": "published"}, headers=auth)
    client.post(f"{base}/posts", json={"title": "Borrador"}, headers=auth)

    ok = FakeBuilder()
    app.dependency_overrides[get_builder_client] = lambda: ok
    try:
        r = client.post("/api/build", json={"blogId": b["id"]}, headers=auth)
        assert r.status_code == 201 and r.json()["result"] == {"files": ["index.html"]}
        assert [p["title"] for p in ok.received["posts"]] == ["Visible"]

        r = client.post("/api/build", json={"blogId": b["id"], "includeDrafts": True}, headers=auth)
        assert len(ok.received["posts"]) == 2

        app.dependency_overrides[get_builder_client] = lambda: FakeBuilder(fail=True)
        r = client.post("/api/build", json={"blogId": b["id"]}, headers=auth)
        assert r.status_code == 502
        detail = r.json()["details"]
        assert "Builder caído" in detail["message"]
        failed = client.get(f"/api/builds/{detail['buildId']}", headers=auth).json()
        assert failed["status"] == "failed"
    finally:
        app.dependency_overrides.clear()


def test_blog_ownership_is_enforced_by_service(client, auth):
    from app.database import SessionLocal
    from app.models import User
    from app.security import hash_password

    with SessionLocal() as db:
        db.add(User(email="otro@example.com", name="Otro", password_hash=hash_password("clave12345")))
        db.commit()
    token = client.post("/api/auth/login", json={"email": "otro@example.com", "password": "clave12345"}).json()["accessToken"]
    other = {"Authorization": f"Bearer {token}"}

    mine = client.post("/api/blogs", json={"name": "Privado"}, headers=auth).json()
    assert client.get(f"/api/blogs/{mine['id']}", headers=other).status_code == 404
    assert client.get(f"/api/blogs/{mine['id']}/pages", headers=other).status_code == 404
    assert client.post("/api/build", json={"blogId": mine["id"]}, headers=other).status_code == 404
    assert client.get("/api/blogs", headers=other).json() == []
