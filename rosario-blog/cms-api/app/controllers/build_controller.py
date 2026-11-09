from fastapi import APIRouter, Depends, Query

from ..dependencies import get_build_service, get_current_user
from ..models import User
from ..models.schemas import BuildIn, BuildOut
from ..services.build_service import BuildService

router = APIRouter(tags=["build"])


@router.post("/build", response_model=BuildOut, status_code=201)
def create_build(body: BuildIn, service: BuildService = Depends(get_build_service),
                 user: User = Depends(get_current_user)):
    return service.build(body.blog_id, body.include_drafts, user)


@router.get("/builds/{build_id}", response_model=BuildOut)
def read_build(build_id: int, service: BuildService = Depends(get_build_service),
               user: User = Depends(get_current_user)):
    return service.get(build_id, user)


@router.get("/blogs/{blog_id}/preview", response_model=BuildOut)
def preview(blog_id: int, service: BuildService = Depends(get_build_service),
            user: User = Depends(get_current_user)):
    return service.preview(blog_id, user)


@router.get("/blogs/{blog_id}/builds", response_model=list[BuildOut])
def list_builds(blog_id: int, limit: int = Query(20, ge=1, le=100), service: BuildService = Depends(get_build_service),
                user: User = Depends(get_current_user)):
    return service.list_builds(blog_id, user, limit)
