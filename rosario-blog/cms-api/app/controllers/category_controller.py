from fastapi import APIRouter, Depends, Response

from ..dependencies import get_category_service, get_current_user
from ..models import User
from ..models.schemas import CategoryIn, CategoryOut
from ..services.category_service import CategoryService

router = APIRouter(prefix="/blogs/{blog_id}/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(blog_id: int, service: CategoryService = Depends(get_category_service),
                    user: User = Depends(get_current_user)):
    return service.list_categories(blog_id, user)


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(blog_id: int, body: CategoryIn,
                    service: CategoryService = Depends(get_category_service),
                    user: User = Depends(get_current_user)):
    return service.create(blog_id, body, user)


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(blog_id: int, category_id: int, body: CategoryIn,
                    service: CategoryService = Depends(get_category_service),
                    user: User = Depends(get_current_user)):
    return service.update(blog_id, category_id, body, user)


@router.delete("/{category_id}", status_code=204)
def delete_category(blog_id: int, category_id: int,
                    service: CategoryService = Depends(get_category_service),
                    user: User = Depends(get_current_user)):
    service.delete(blog_id, category_id, user)
    return Response(status_code=204)
