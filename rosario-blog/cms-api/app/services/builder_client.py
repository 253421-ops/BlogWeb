import time

import httpx

from ..security import service_token

WARMUP_TRIES = 3        # intentos de «despertar» al generador (el plan gratis de Render lo duerme)
WARMUP_PAUSE = 10.0     # segundos entre intentos
TIMEOUT = 120.0         # el build puede tardar si el generador acaba de despertar
RETRY_STATUS = {502, 503, 504}   # respuestas típicas de «todavía estoy despertando»


class BuilderClient:
    """Cliente HTTP hacia la API del generador: le entrega el contenido y el generador publica el sitio.

    Antes de enviar el paquete hace un *warm-up* (GET /health con reintentos): así el primer «Publicar sitio»
    del día no se pierde con un 502 mientras Render despierta el servicio (tarda ~50 s)."""

    def __init__(self, base_url: str = "", *, sleep=time.sleep, transport: httpx.BaseTransport | None = None):
        self.base_url = base_url.rstrip("/")
        self._sleep = sleep
        self._transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=TIMEOUT, transport=self._transport)

    def warm_up(self, client: httpx.Client) -> bool:
        """Pide /health hasta que el generador responda 200. Devuelve False si no despertó (igual se intenta el build)."""
        for attempt in range(WARMUP_TRIES):
            try:
                if client.get(f"{self.base_url}/health", timeout=20.0).status_code == 200:
                    return True
            except httpx.HTTPError:
                pass
            if attempt < WARMUP_TRIES - 1:
                self._sleep(WARMUP_PAUSE)
        return False

    def build(self, bundle: dict) -> dict:
        if not self.base_url:
            return {"simulated": True, "pages": len(bundle["pages"]), "posts": len(bundle["posts"]),
                    "message": "GENERATOR_URL no configurado: build simulado"}
        token = service_token("builds:write")
        with self._client() as client:
            self.warm_up(client)
            for attempt in range(WARMUP_TRIES):
                resp = client.post(f"{self.base_url}/api/v1/builds", json={"reason": "cms", "bundle": bundle},
                                   headers={"Authorization": f"Bearer {token}"})
                if resp.status_code in RETRY_STATUS and attempt < WARMUP_TRIES - 1:
                    self._sleep(WARMUP_PAUSE)        # sigue despertando: espera y reintenta
                    continue
                resp.raise_for_status()
                return resp.json()
        raise RuntimeError("El generador no respondió")  # no se alcanza: el último intento siempre devuelve o lanza
