from fastapi import APIRouter, Depends

from ..dependencies import get_current_user, get_metrics_service
from ..models import User
from ..models.schemas import MetricsOut
from ..services.metrics_service import MetricsService

router = APIRouter(tags=["metrics"])


@router.get("/blogs/{blog_id}/metrics", response_model=MetricsOut)
def blog_metrics(blog_id: int, service: MetricsService = Depends(get_metrics_service),
                 user: User = Depends(get_current_user)):
    return service.get_metrics(blog_id, user)
