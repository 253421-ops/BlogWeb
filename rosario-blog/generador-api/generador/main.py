"""Arranque:  uvicorn generador.main:create_app --factory --port 8013"""
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import sessionmaker

from generador.config import Settings
from generador.controllers import builds_controller
from generador.models import Base
from generador.repository.builds_repository import BuildsRepository
from common.app_factory import create_base_app
from common.db import make_engine
from common.rate_limit import RateLimiter
from common.timeutil import to_iso, utcnow


def create_app(settings=None, engine=None, sync_builds=False):
    settings = settings or Settings()
    engine = engine or make_engine(settings.database_url)
    Base.metadata.create_all(engine)
    app = create_base_app("generator", settings, "Generador: convierte el contenido que le envía el CMS en el sitio estático y su API estática.")
    app.state.limiter = RateLimiter(settings.rate_limit_user_per_min, settings.rate_limit_service_per_min)
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.bundles = {}                      # build_id -> contenido recibido del CMS (en memoria)
    app.state.sync_builds = sync_builds
    with app.state.session_factory() as session:
        BuildsRepository(session).fail_interrupted(to_iso(utcnow()))      # lo que quedó "RUNNING" tras un reinicio
    app.include_router(builds_controller.router)
    Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
    app.mount("/site", StaticFiles(directory=settings.output_dir, html=True), name="site")   # el blog generado, visible en /site/
    return app
