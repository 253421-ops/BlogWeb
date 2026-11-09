import httpx

from ..security import service_token


class BuilderClient:
    """Cliente HTTP hacia la API del generador: le entrega el contenido y el generador publica el sitio."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip("/")

    def build(self, bundle: dict) -> dict:
        if not self.base_url:
            return {"simulated": True, "pages": len(bundle["pages"]), "posts": len(bundle["posts"]),
                    "message": "GENERATOR_URL no configurado: build simulado"}
        token = service_token("builds:write")
        resp = httpx.post(f"{self.base_url}/api/v1/builds", json={"reason": "cms", "bundle": bundle},
                          headers={"Authorization": f"Bearer {token}"}, timeout=30)
        resp.raise_for_status()
        return resp.json()
