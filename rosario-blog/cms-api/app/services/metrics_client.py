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
        out = {"visitas": data["views_total"], "visitantesUnicos": data["unique_visitors"], "simulated": False,
               "sesiones": data.get("sessions", 0), "tiempoMedioSeg": data.get("avg_dwell_time_sec", 0),
               "reboteBp": data.get("bounce_rate_bp", 0), "dispositivos": data.get("devices") or {},
               "porDia": [], "paginas": []}
        for key, path, field in (("porDia", "timeseries", "items"), ("paginas", "pages", "items")):   # extras: si fallan, el resumen sigue sirviendo
            try:
                r = httpx.get(f"{self.base_url}/api/v1/metrics/{path}", headers={"Authorization": f"Bearer {token}"}, timeout=10)
                r.raise_for_status()
                out[key] = r.json().get(field, [])
            except Exception:  # noqa: BLE001
                pass
        return out
