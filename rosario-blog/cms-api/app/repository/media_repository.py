from sqlalchemy import select

from ..models import Media
from .base import BlogScopedRepository


class MediaRepository(BlogScopedRepository[Media]):
    model = Media

    def list_by_blog(self, blog_id: int) -> list[Media]:
        q = select(Media).where(Media.blog_id == blog_id).order_by(Media.id.desc())
        return list(self.db.scalars(q).all())
