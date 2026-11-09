from ..exceptions import ExternalServiceError, NotFoundError
from ..models import Blog, Build, User, now
from ..models.schemas import BlogOut, CategoryOut, PageOut, PostSummary
from ..repository.build_repository import BuildRepository
from ..repository.category_repository import CategoryRepository
from ..repository.page_repository import PageRepository
from ..repository.post_repository import PostRepository
from .blog_service import BlogService
from .builder_client import BuilderClient


def _dump(schema, obj) -> dict:
    return schema.model_validate(obj).model_dump(mode="json", by_alias=True)


class BuildService:
    """Interfaz → CMS → Builder → Astro. Arma el contenido y delega la construcción."""

    def __init__(self, builds: BuildRepository, blogs: BlogService, pages: PageRepository,
                 posts: PostRepository, categories: CategoryRepository, builder: BuilderClient):
        self.builds = builds
        self.blogs = blogs
        self.pages = pages
        self.posts = posts
        self.categories = categories
        self.builder = builder

    def build(self, blog_id: int, include_drafts: bool, user: User) -> Build:
        blog = self.blogs.get_owned(blog_id, user)
        build = self.builds.save(Build(blog_id=blog.id, status="running"))
        try:
            build.result = self.builder.build(self._make_bundle(blog, include_drafts))
            build.status = "success"
        except Exception as exc:  # el Builder cayó, respondió error, etc.
            build.status = "failed"
            build.message = str(exc)[:500]
        build.finished_at = now()
        self.builds.save(build)

        if build.status == "failed":
            raise ExternalServiceError({"buildId": build.id, "message": build.message})
        return build

    def list_builds(self, blog_id: int, user: User, limit: int) -> list[Build]:
        blog = self.blogs.get_owned(blog_id, user)
        return self.builds.latest(blog.id, limit)

    def get(self, build_id: int, user: User) -> Build:
        build = self.builds.get(build_id)
        if build is None:
            raise NotFoundError("Build no encontrado")
        self.blogs.get_owned(build.blog_id, user)
        return build

    def preview(self, blog_id: int, user: User) -> Build:
        """Último sitio generado con éxito, para el previsualizador."""
        blog = self.blogs.get_owned(blog_id, user)
        build = self.builds.latest_success(blog.id)
        if build is None:
            raise NotFoundError("Aún no hay un sitio generado: ejecuta POST /api/build")
        return build

    def _make_bundle(self, blog: Blog, include_drafts: bool) -> dict:
        keep = lambda status: include_drafts or status == "published"
        return {
            "blog": _dump(BlogOut, blog),
            "pages": [_dump(PageOut, p) for p in self.pages.list_by_blog(blog.id) if keep(p.status)],
            "posts": [
                {**_dump(PostSummary, p), "content": p.content}
                for p in self.posts.list_by_blog(blog.id)
                if keep(p.status)
            ],
            "categories": [_dump(CategoryOut, c) for c in self.categories.list_by_blog(blog.id)],
        }
