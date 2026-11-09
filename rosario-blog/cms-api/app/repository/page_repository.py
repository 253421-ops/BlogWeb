from sqlalchemy import select

from ..models import Page
from .base import BlogScopedRepository


class PageRepository(BlogScopedRepository[Page]):
    model = Page

    def landing_exists(self, blog_id: int, exclude_id: int | None = None) -> bool:
        q = select(Page.id).where(Page.blog_id == blog_id, Page.type == "landing")
        if exclude_id is not None:
            q = q.where(Page.id != exclude_id)
        return self.db.scalar(q) is not None
