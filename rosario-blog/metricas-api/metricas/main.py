"""Arranque:  uvicorn metricas.main:create_app --factory --port 8012"""
from sqlalchemy.orm import sessionmaker

from metricas.config import Settings
from metricas.controllers import metrics_controller
from metricas.models import Base
from common.app_factory import create_base_app
from common.db import make_engine
from common.rate_limit import RateLimiter
from common.timeutil import utcnow


def create_app(settings=None, engine=None, clock=None):
    settings = settings or Settings()
    engine = engine or make_engine(settings.database_url)
    Base.metadata.create_all(engine)
    app = create_base_app("metrics", settings, "Métricas: recolecta eventos de interacción del sitio y entrega reportes.")
    app.state.limiter = RateLimiter(settings.reports_limit_per_min, settings.reports_limit_per_min)
    app.state.ingest_limiter = RateLimiter(settings.ingest_limit_per_min, settings.ingest_limit_per_min)
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.clock = clock or utcnow
    app.include_router(metrics_controller.router)
    return app
