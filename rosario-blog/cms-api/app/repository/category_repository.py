from sqlalchemy import select

from ..models import Category
from .base import BlogScopedRepository


class CategoryRepository(BlogScopedRepository[Category]):
    model = Category

    def list_by_blog(self, blog_id: int) -> list[Category]:
        q = select(Category).where(Category.blog_id == blog_id).order_by(Category.name)
        return list(self.db.scalars(q).all())
