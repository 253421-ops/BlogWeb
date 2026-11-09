from sqlalchemy import func, or_, select

from ..models import Post
from .base import BlogScopedRepository


class PostRepository(BlogScopedRepository[Post]):
    model = Post

    def search(
        self,
        blog_id: int,
        status: str | None,
        category_id: int | None,
        page: int,
        limit: int,
        q: str | None = None,
    ) -> tuple[list[Post], int]:
        text = q
        q = select(Post).where(Post.blog_id == blog_id)
        if text:
            like = f"%{text}%"
            q = q.where(or_(Post.title.ilike(like), Post.excerpt.ilike(like), Post.content.ilike(like)))
        if status:
            q = q.where(Post.status == status)
        if category_id is not None:
            q = q.where(Post.category_id == category_id)
        total = self.db.scalar(select(func.count()).select_from(q.subquery()))
        items = self.db.scalars(
            q.order_by(Post.created_at.desc(), Post.id.desc()).offset((page - 1) * limit).limit(limit)
        ).all()
        return list(items), total
