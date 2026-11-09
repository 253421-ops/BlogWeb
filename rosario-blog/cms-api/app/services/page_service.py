from ..exceptions import ConflictError, NotFoundError
from ..models import Page, User
from ..models.schemas import PageIn
from ..repository.page_repository import PageRepository
from .blog_service import BlogService
from .slugs import make_slug, slugify

SLUG_TAKEN = "Ya existe una página con ese slug en este blog"


class PageService:
    def __init__(self, pages: PageRepository, blogs: BlogService):
        self.pages = pages
        self.blogs = blogs

    def list_pages(self, blog_id: int, user: User) -> list[Page]:
        blog = self.blogs.get_owned(blog_id, user)
        return self.pages.list_by_blog(blog.id)

    def get(self, blog_id: int, page_id: int, user: User) -> Page:
        blog = self.blogs.get_owned(blog_id, user)
        page = self.pages.get_in_blog(blog.id, page_id)
        if page is None:
            raise NotFoundError("Página no encontrada")
        return page

    def create(self, blog_id: int, data: PageIn, user: User) -> Page:
        blog = self.blogs.get_owned(blog_id, user)
        self._check_single_landing(blog.id, data.type)
        slug = data.slug or make_slug(slugify(data.title), lambda s: self.pages.slug_exists(blog.id, s))
        page = Page(blog_id=blog.id, slug=slug, title=data.title, type=data.type,
                    content=data.content, status=data.status)
        return self.pages.save(page, SLUG_TAKEN)

    def update(self, blog_id: int, page_id: int, data: PageIn, user: User) -> Page:
        page = self.get(blog_id, page_id, user)
        self._check_single_landing(blog_id, data.type, exclude_id=page.id)
        page.title, page.type, page.content, page.status = data.title, data.type, data.content, data.status
        if data.slug:
            page.slug = data.slug
        return self.pages.save(page, SLUG_TAKEN)

    def delete(self, blog_id: int, page_id: int, user: User) -> None:
        self.pages.delete(self.get(blog_id, page_id, user))

    def _check_single_landing(self, blog_id: int, page_type: str, exclude_id: int | None = None) -> None:
        if page_type == "landing" and self.pages.landing_exists(blog_id, exclude_id):
            raise ConflictError("El blog ya tiene una landing")
