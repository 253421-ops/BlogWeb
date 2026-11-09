from sqlalchemy import select

from ..models import Blog
from .base import BaseRepository


class BlogRepository(BaseRepository[Blog]):
    model = Blog

    def list_by_owner(self, owner_id: int) -> list[Blog]:
        q = select(Blog).where(Blog.owner_id == owner_id).order_by(Blog.id)
        return list(self.db.scalars(q).all())

    def slug_exists(self, slug: str) -> bool:
        return self.db.scalar(select(Blog.id).where(Blog.slug == slug)) is not None
