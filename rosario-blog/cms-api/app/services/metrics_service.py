from ..exceptions import ExternalServiceError
from ..models import User
from .blog_service import BlogService
from .metrics_client import MetricsClient


class MetricsService:
    def __init__(self, blogs: BlogService, client: MetricsClient):
        self.blogs = blogs
        self.client = client

    def get_metrics(self, blog_id: int, user: User) -> dict:
        blog = self.blogs.get_owned(blog_id, user)
        try:
            return self.client.fetch(blog.id)
        except Exception as exc:
            raise ExternalServiceError(f"No se pudieron consultar las métricas: {exc}")
