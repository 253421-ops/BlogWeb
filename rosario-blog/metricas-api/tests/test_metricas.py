import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from common.db import make_engine
from common.security import sign_token
from metricas.config import Settings
from metricas.main import create_app

SECRET = "secreto-de-prueba-0123456789-0123456789"
H = lambda scope, sub="admin": {"Authorization": f"Bearer {sign_token(SECRET, sub, scope)}"}
UA = "Mozilla/5.0 (Windows NT 10.0) Chrome/120"


def ev(type_, session, **kw):
    return {"event_id": str(uuid.uuid4()), "type": type_, "session_id": session, "visitor_id": session, "path": "/site/posts/hola/", "post_slug": "hola", **kw}


def test_metricas_ingesta_validacion_y_reportes():
    now = {"t": datetime(2026, 10, 20, 12, tzinfo=timezone.utc)}
    c = TestClient(create_app(Settings(jwt_secret=SECRET), make_engine("sqlite://"), lambda: now["t"]))
    s1, s2 = str(uuid.uuid4()), str(uuid.uuid4())
    e = ev("page_view", s1, referrer_host="instagram.com")
    assert c.post("/api/v1/events", json={"events": [e]}, headers={"User-Agent": UA}).json() == {"received": 1, "stored": 1}
    assert c.post("/api/v1/events", json={"events": [e]}, headers={"User-Agent": UA}).json()["stored"] == 0     # reintento: no duplica
    c.post("/api/v1/events", json={"events": [ev("time_on_page", s1, value=60), ev("page_view", s2), ev("scroll_depth", s2, value=50)]}, headers={"User-Agent": UA})
    assert c.post("/api/v1/events", json={"events": [ev("page_view", s2)]}, headers={"User-Agent": "Googlebot/2.1"}).json()["stored"] == 0   # robots
    assert c.get("/api/v1/metrics/overview").status_code == 401
    assert c.get("/api/v1/metrics/overview", headers=H("posts:read")).status_code == 403
    o = c.get("/api/v1/metrics/overview", headers=H("metrics:read")).json()
    assert o["views_total"] == 2 and o["unique_visitors"] == 2
    assert c.get("/api/v1/metrics/overview?from=2026-02-30", headers=H("metrics:read")).status_code == 422
