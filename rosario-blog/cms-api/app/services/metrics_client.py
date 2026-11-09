import httpx

from ..security import service_token


class MetricsClient:
    """Cliente REST hacia la API de métricas (GET /api/v1/metrics/overview)."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip("/")

    def fetch(self, blog_id: int) -> dict:
        if not self.base_url:
            return {"visitas": 0, "visitantesUnicos": 0, "simulated": True}
        token = service_token("metrics:read")
        resp = httpx.get(f"{self.base_url}/api/v1/metrics/overview", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {"visitas": data["views_total"], "visitantesUnicos": data["unique_visitors"], "simulated": False}
