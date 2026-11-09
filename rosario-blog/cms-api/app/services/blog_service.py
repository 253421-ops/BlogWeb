from ..exceptions import NotFoundError
from ..models import Blog, User
from ..models.schemas import BlogIn
from ..repository.blog_repository import BlogRepository
from .slugs import make_slug, slugify

SLUG_TAKEN = "Ya existe un blog con ese slug"


class BlogService:
    def __init__(self, blogs: BlogRepository):
        self.blogs = blogs

    def list_blogs(self, user: User) -> list[Blog]:
        return self.blogs.list_by_owner(user.id)

    def get_owned(self, blog_id: int, user: User) -> Blog:
        """Regla de negocio: un usuario solo accede a sus propios blogs."""
        blog = self.blogs.get(blog_id)
        if blog is None or blog.owner_id != user.id:
            raise NotFoundError("Blog no encontrado")
        return blog

    def create(self, data: BlogIn, user: User) -> Blog:
        slug = data.slug or make_slug(slugify(data.name), self.blogs.slug_exists)
        blog = Blog(owner_id=user.id, name=data.name, slug=slug, description=data.description)
        return self.blogs.save(blog, SLUG_TAKEN)

    def update(self, blog_id: int, data: BlogIn, user: User) -> Blog:
        blog = self.get_owned(blog_id, user)
        blog.name = data.name
        blog.description = data.description
        if data.slug:
            blog.slug = data.slug
        return self.blogs.save(blog, SLUG_TAKEN)

    def delete(self, blog_id: int, user: User) -> None:
        self.blogs.delete(self.get_owned(blog_id, user))
