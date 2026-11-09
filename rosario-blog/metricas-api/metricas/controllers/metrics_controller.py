"""CONTROLLER de métricas: la ingesta es PÚBLICA (los visitantes no tienen token); los reportes exigen JWT."""
from fastapi import APIRouter, Depends, Query, Request

from metricas.schemas import IngestIn, IngestOut
from metricas.services.metrics_service import MetricsService
from common.db import get_session
from common.rate_limit import RateLimiter
from common.security import Principal, require_scope
from metricas.repository.events_repository import EventsRepository

router = APIRouter(prefix="/api/v1", tags=["métricas"])
DAY = r"^\d{4}-\d{2}-\d{2}$"


def get_service(request: Request, session=Depends(get_session)) -> MetricsService:
    return MetricsService(EventsRepository(session), request.app.state.clock)


@router.post("/events", status_code=202, response_model=IngestOut, summary="Enviar eventos (público, sin token)")
def ingest(payload: IngestIn, request: Request, service: MetricsService = Depends(get_service)):
    ip = request.client.host if request.client else "?"
    request.app.state.ingest_limiter.check(Principal(ip, frozenset(), "user"))      # límite por IP
    return service.ingest(payload.events, request.headers.get("user-agent", ""))


@router.get("/metrics/overview", summary="Resumen: vistas, únicos, tiempo, rebote, dispositivos, referentes")
def overview(date_from: str | None = Query(None, alias="from", pattern=DAY), date_to: str | None = Query(None, alias="to", pattern=DAY),
             _=Depends(require_scope("metrics:read")), service: MetricsService = Depends(get_service)):
    return service.overview(date_from, date_to)


@router.get("/metrics/pages", summary="Páginas más vistas")
def pages(limit: int = Query(10, ge=1, le=100), date_from: str | None = Query(None, alias="from", pattern=DAY),
          date_to: str | None = Query(None, alias="to", pattern=DAY), _=Depends(require_scope("metrics:read")), service: MetricsService = Depends(get_service)):
    return service.pages(date_from, date_to, limit)


@router.get("/metrics/timeseries", summary="Vistas por día (los días sin datos aparecen con 0)")
def timeseries(date_from: str | None = Query(None, alias="from", pattern=DAY), date_to: str | None = Query(None, alias="to", pattern=DAY),
               _=Depends(require_scope("metrics:read")), service: MetricsService = Depends(get_service)):
    return service.timeseries(date_from, date_to)
