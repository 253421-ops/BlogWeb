from fastapi import APIRouter, Depends, Response

from ..dependencies import get_current_user, get_page_service
from ..models import User
from ..models.schemas import PageIn, PageOut
from ..services.page_service import PageService

router = APIRouter(prefix="/blogs/{blog_id}/pages", tags=["pages"])


@router.get("", response_model=list[PageOut])
def list_pages(blog_id: int, service: PageService = Depends(get_page_service),
               user: User = Depends(get_current_user)):
    return service.list_pages(blog_id, user)


@router.post("", response_model=PageOut, status_code=201)
def create_page(blog_id: int, body: PageIn, service: PageService = Depends(get_page_service),
                user: User = Depends(get_current_user)):
    return service.create(blog_id, body, user)


@router.get("/{page_id}", response_model=PageOut)
def read_page(blog_id: int, page_id: int, service: PageService = Depends(get_page_service),
              user: User = Depends(get_current_user)):
    return service.get(blog_id, page_id, user)


@router.put("/{page_id}", response_model=PageOut)
def update_page(blog_id: int, page_id: int, body: PageIn, service: PageService = Depends(get_page_service),
                user: User = Depends(get_current_user)):
    return service.update(blog_id, page_id, body, user)


@router.delete("/{page_id}", status_code=204)
def delete_page(blog_id: int, page_id: int, service: PageService = Depends(get_page_service),
                user: User = Depends(get_current_user)):
    service.delete(blog_id, page_id, user)
    return Response(status_code=204)
