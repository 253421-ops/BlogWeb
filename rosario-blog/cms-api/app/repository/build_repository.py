from sqlalchemy import select

from ..models import Build
from .base import BlogScopedRepository


class BuildRepository(BlogScopedRepository[Build]):
    model = Build

    def latest_success(self, blog_id: int) -> Build | None:
        q = (
            select(Build)
            .where(Build.blog_id == blog_id, Build.status == "success")
            .order_by(Build.id.desc())
        )
        return self.db.scalar(q)

    def latest(self, blog_id: int, limit: int) -> list[Build]:
        q = select(Build).where(Build.blog_id == blog_id).order_by(Build.id.desc()).limit(limit)
        return list(self.db.scalars(q).all())
