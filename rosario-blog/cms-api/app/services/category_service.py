from ..exceptions import NotFoundError
from ..models import Category, User
from ..models.schemas import CategoryIn
from ..repository.category_repository import CategoryRepository
from .blog_service import BlogService
from .slugs import make_slug, slugify

SLUG_TAKEN = "Ya existe una categoría con ese slug"


class CategoryService:
    def __init__(self, categories: CategoryRepository, blogs: BlogService):
        self.categories = categories
        self.blogs = blogs

    def list_categories(self, blog_id: int, user: User) -> list[Category]:
        blog = self.blogs.get_owned(blog_id, user)
        return self.categories.list_by_blog(blog.id)

    def _get(self, blog_id: int, category_id: int, user: User) -> Category:
        blog = self.blogs.get_owned(blog_id, user)
        category = self.categories.get_in_blog(blog.id, category_id)
        if category is None:
            raise NotFoundError("Categoría no encontrada")
        return category

    def create(self, blog_id: int, data: CategoryIn, user: User) -> Category:
        blog = self.blogs.get_owned(blog_id, user)
        slug = data.slug or make_slug(slugify(data.name), lambda s: self.categories.slug_exists(blog.id, s))
        return self.categories.save(Category(blog_id=blog.id, name=data.name, slug=slug), SLUG_TAKEN)

    def update(self, blog_id: int, category_id: int, data: CategoryIn, user: User) -> Category:
        category = self._get(blog_id, category_id, user)
        category.name = data.name
        if data.slug:
            category.slug = data.slug
        return self.categories.save(category, SLUG_TAKEN)

    def delete(self, blog_id: int, category_id: int, user: User) -> None:
        self.categories.delete(self._get(blog_id, category_id, user))
