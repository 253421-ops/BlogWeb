from fastapi import APIRouter, Depends, Query, Response

from ..dependencies import get_current_user, get_post_service
from ..models import User
from ..models.schemas import PostIn, PostList, PostOut, Status, StatusIn
from ..services.post_service import PostService

router = APIRouter(prefix="/blogs/{blog_id}/posts", tags=["posts"])


@router.get("", response_model=PostList)
def list_posts(
    blog_id: int,
    status: Status | None = None,
    category_id: int | None = Query(None, alias="categoryId"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, max_length=100),
    service: PostService = Depends(get_post_service),
    user: User = Depends(get_current_user),
):
    items, total = service.list_posts(blog_id, user, status, category_id, page, limit, q)
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("", response_model=PostOut, status_code=201)
def create_post(blog_id: int, body: PostIn, service: PostService = Depends(get_post_service),
                user: User = Depends(get_current_user)):
    return service.create(blog_id, body, user)


@router.get("/{post_id}", response_model=PostOut)
def read_post(blog_id: int, post_id: int, service: PostService = Depends(get_post_service),
              user: User = Depends(get_current_user)):
    return service.get(blog_id, post_id, user)


@router.put("/{post_id}", response_model=PostOut)
def update_post(blog_id: int, post_id: int, body: PostIn, service: PostService = Depends(get_post_service),
                user: User = Depends(get_current_user)):
    return service.update(blog_id, post_id, body, user)


@router.patch("/{post_id}/status", response_model=PostOut)
def change_status(blog_id: int, post_id: int, body: StatusIn,
                  service: PostService = Depends(get_post_service),
                  user: User = Depends(get_current_user)):
    return service.change_status(blog_id, post_id, body.status, user)


@router.delete("/{post_id}", status_code=204)
def delete_post(blog_id: int, post_id: int, service: PostService = Depends(get_post_service),
                user: User = Depends(get_current_user)):
    service.delete(blog_id, post_id, user)
    return Response(status_code=204)
