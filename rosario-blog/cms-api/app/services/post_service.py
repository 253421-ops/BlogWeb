from ..exceptions import InvalidDataError, NotFoundError
from ..models import Post, User, now
from ..models.schemas import PostIn
from ..repository.category_repository import CategoryRepository
from ..repository.post_repository import PostRepository
from .blog_service import BlogService
from .slugs import make_slug, slugify

SLUG_TAKEN = "Ya existe una publicación con ese slug en este blog"


class PostService:
    def __init__(self, posts: PostRepository, categories: CategoryRepository, blogs: BlogService):
        self.posts = posts
        self.categories = categories
        self.blogs = blogs

    def list_posts(self, blog_id: int, user: User, status: str | None, category_id: int | None,
                   page: int, limit: int, q: str | None = None) -> tuple[list[Post], int]:
        blog = self.blogs.get_owned(blog_id, user)
        return self.posts.search(blog.id, status, category_id, page, limit, q)

    def get(self, blog_id: int, post_id: int, user: User) -> Post:
        blog = self.blogs.get_owned(blog_id, user)
        post = self.posts.get_in_blog(blog.id, post_id)
        if post is None:
            raise NotFoundError("Publicación no encontrada")
        return post

    def create(self, blog_id: int, data: PostIn, user: User) -> Post:
        blog = self.blogs.get_owned(blog_id, user)
        self._check_category(blog.id, data.category_id)
        slug = data.slug or make_slug(slugify(data.title), lambda s: self.posts.slug_exists(blog.id, s))
        post = Post(blog_id=blog.id, slug=slug, title=data.title, excerpt=data.excerpt,
                    content=data.content, cover_url=data.cover_url, category_id=data.category_id)
        self._apply_status(post, data.status)
        return self.posts.save(post, SLUG_TAKEN)

    def update(self, blog_id: int, post_id: int, data: PostIn, user: User) -> Post:
        post = self.get(blog_id, post_id, user)
        self._check_category(blog_id, data.category_id)
        post.title, post.excerpt, post.content = data.title, data.excerpt, data.content
        post.cover_url, post.category_id = data.cover_url, data.category_id
        if data.slug:
            post.slug = data.slug
        self._apply_status(post, data.status)
        return self.posts.save(post, SLUG_TAKEN)

    def change_status(self, blog_id: int, post_id: int, status: str, user: User) -> Post:
        post = self.get(blog_id, post_id, user)
        self._apply_status(post, status)
        return self.posts.save(post)

    def delete(self, blog_id: int, post_id: int, user: User) -> None:
        self.posts.delete(self.get(blog_id, post_id, user))

    # --- reglas internas ---
    def _check_category(self, blog_id: int, category_id: int | None) -> None:
        if category_id is not None and self.categories.get_in_blog(blog_id, category_id) is None:
            raise InvalidDataError("La categoría no pertenece a este blog")

    @staticmethod
    def _apply_status(post: Post, status: str) -> None:
        post.status = status
        if status == "published":
            post.published_at = post.published_at or now()
        else:
            post.published_at = None
