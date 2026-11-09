from fastapi import APIRouter, Depends, Response

from ..dependencies import get_blog_service, get_current_user
from ..models import User
from ..models.schemas import BlogIn, BlogOut
from ..services.blog_service import BlogService

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get("", response_model=list[BlogOut])
def list_blogs(service: BlogService = Depends(get_blog_service), user: User = Depends(get_current_user)):
    return service.list_blogs(user)


@router.post("", response_model=BlogOut, status_code=201)
def create_blog(body: BlogIn, service: BlogService = Depends(get_blog_service),
                user: User = Depends(get_current_user)):
    return service.create(body, user)


@router.get("/{blog_id}", response_model=BlogOut)
def read_blog(blog_id: int, service: BlogService = Depends(get_blog_service),
              user: User = Depends(get_current_user)):
    return service.get_owned(blog_id, user)


@router.put("/{blog_id}", response_model=BlogOut)
def update_blog(blog_id: int, body: BlogIn, service: BlogService = Depends(get_blog_service),
                user: User = Depends(get_current_user)):
    return service.update(blog_id, body, user)


@router.delete("/{blog_id}", status_code=204)
def delete_blog(blog_id: int, service: BlogService = Depends(get_blog_service),
                user: User = Depends(get_current_user)):
    service.delete(blog_id, user)
    return Response(status_code=204)
