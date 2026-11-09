"""CONTROLLER de compilaciones."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from generador.repository.builds_repository import BuildsRepository
from generador.services.builds_service import BuildsService
from common.db import get_session
from common.security import require_scope

router = APIRouter(prefix="/api/v1/builds", tags=["compilaciones"])


class BuildRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(default="manual", min_length=1, max_length=100)
    bundle: dict | None = Field(default=None, description="Contenido del blog que arma el CMS: {blog, pages, posts, categories}")


class BuildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    build_id: str
    status: str
    reason: str
    post_id: str | None = None
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    pages_generated: int | None = None
    error_code: str | None = None
    error_message: str | None = None


class BuildListOut(BaseModel):
    items: list[BuildOut]


def get_service(request: Request, session=Depends(get_session)) -> BuildsService:
    return BuildsService(BuildsRepository(session), request.app)


@router.post("", status_code=202, summary="Pedir una compilación del sitio (responde 202 y compila en segundo plano)")
def request_build(payload: BuildRequest | None = None, _=Depends(require_scope("builds:write")), service: BuildsService = Depends(get_service)):
    payload = payload or BuildRequest()
    job, coalesced = service.enqueue(payload.reason, payload.bundle)
    return JSONResponse(status_code=202, headers={"Location": f"/api/v1/builds/{job.build_id}"},
                        content={"build_id": job.build_id, "status": job.status, "created_at": job.created_at, "coalesced": coalesced})


@router.get("", response_model=BuildListOut, response_model_exclude_none=True, summary="Listar compilaciones (más nuevas primero)")
def list_builds(limit: int = Query(20, ge=1, le=100), _=Depends(require_scope("builds:read")), service: BuildsService = Depends(get_service)):
    return service.list(limit)


@router.get("/latest", response_model=BuildOut, response_model_exclude_none=True, summary="Última compilación")
def latest_build(_=Depends(require_scope("builds:read")), service: BuildsService = Depends(get_service)):
    return service.latest()


@router.get("/{build_id}", response_model=BuildOut, response_model_exclude_none=True, summary="Consultar una compilación")
def get_build(build_id: UUID, _=Depends(require_scope("builds:read")), service: BuildsService = Depends(get_service)):
    return service.get(str(build_id))
