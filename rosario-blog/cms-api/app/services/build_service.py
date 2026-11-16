import base64
import re

from ..exceptions import ExternalServiceError, NotFoundError
from ..models import Blog, Build, User, now
from ..models.schemas import BlogOut, CategoryOut, PageOut, PostSummary
from ..repository.build_repository import BuildRepository
from ..repository.category_repository import CategoryRepository
from ..repository.media_repository import MediaRepository
from ..repository.page_repository import PageRepository
from ..repository.post_repository import PostRepository
from .blog_service import BlogService
from .builder_client import BuilderClient
from .theme_service import THEME_SLUG, parse_theme, theme_css


def _dump(schema, obj) -> dict:
    return schema.model_validate(obj).model_dump(mode="json", by_alias=True)


class BuildService:
    """Interfaz → CMS → Builder → Astro. Arma el contenido y delega la construcción."""

    def __init__(self, builds: BuildRepository, blogs: BlogService, pages: PageRepository,
                 posts: PostRepository, categories: CategoryRepository, builder: BuilderClient, media: MediaRepository | None = None):
        self.media = media
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
        all_pages = self.pages.list_by_blog(blog.id)
        theme_page = next((p for p in all_pages if p.slug == THEME_SLUG), None)
        theme = parse_theme(theme_page.content if theme_page else None)
        pages_out = [_dump(PageOut, p) for p in all_pages if keep(p.status) and p.slug != THEME_SLUG]
        posts_out = [{**_dump(PostSummary, p), "content": p.content}
                     for p in self.posts.list_by_blog(blog.id) if keep(p.status)]
        return {
            "media": self._media_for(blog.id, [x.get("content") or "" for x in pages_out + posts_out]),
            "blog": _dump(BlogOut, blog),
            "theme": {"scene": theme.scene, "blog": theme.blog},
            "theme_css": theme_css(theme),
            "pages": pages_out,
            "posts": posts_out,
            "categories": [_dump(CategoryOut, c) for c in self.categories.list_by_blog(blog.id)],
        }

    def _media_for(self, blog_id: int, texts: list[str]) -> list[dict]:
        """Las imágenes que usan las entradas viajan dentro del paquete (el Generador está en otro servidor)."""
        if self.media is None:
            return []
        found = sorted(set(re.findall(r"/uploads/%d/([A-Za-z0-9_.-]+)" % blog_id, "\n".join(texts))))
        out = []
        for name in found:
            data = self.media.get_blob(blog_id, name)
            if data is not None:
                out.append({"url": f"/uploads/{blog_id}/{name}", "name": name, "data": base64.b64encode(data).decode()})
        return out
