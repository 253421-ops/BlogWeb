"""App FastAPI base compartida: CORS, manejadores de errores en el formato del contrato y /health."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.handlers import register_error_handlers
from common.timeutil import to_iso, utcnow


def create_base_app(title: str, settings, description: str = "", lifespan=None) -> FastAPI:
    app = FastAPI(title=title, version="1.0.0", description=description, lifespan=lifespan)
    app.state.settings = settings
    if settings.cors_list:
        app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_methods=["*"], allow_headers=["*"], max_age=600)
    register_error_handlers(app)

    @app.get("/health", tags=["sistema"], summary="Estado del servicio (sin token)")
    def health():
        return {"status": "ok", "service": title, "time": to_iso(utcnow())}

    return app
