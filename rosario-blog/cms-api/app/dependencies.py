"""Raíz de composición: arma repositorios y servicios y los inyecta en los controllers."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .exceptions import UnauthorizedError
from .models import User
from .repository.blog_repository import BlogRepository
from .repository.build_repository import BuildRepository
from .repository.category_repository import CategoryRepository
from .repository.media_repository import MediaRepository
from .repository.page_repository import PageRepository
from .repository.post_repository import PostRepository
from .repository.user_repository import UserRepository
from .services.auth_service import AuthService
from .services.blog_service import BlogService
from .services.build_service import BuildService
from .services.builder_client import BuilderClient
from .services.category_service import CategoryService
from .services.media_service import MediaService
from .services.metrics_client import MetricsClient
from .services.metrics_service import MetricsService
from .services.page_service import PageService
from .services.post_service import PostService

bearer = HTTPBearer(auto_error=False)


# --- repositorios ---
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_blog_repository(db: Session = Depends(get_db)) -> BlogRepository:
    return BlogRepository(db)


def get_page_repository(db: Session = Depends(get_db)) -> PageRepository:
    return PageRepository(db)


def get_post_repository(db: Session = Depends(get_db)) -> PostRepository:
    return PostRepository(db)


def get_category_repository(db: Session = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


def get_media_repository(db: Session = Depends(get_db)) -> MediaRepository:
    return MediaRepository(db)


def get_build_repository(db: Session = Depends(get_db)) -> BuildRepository:
    return BuildRepository(db)


# --- clientes hacia las otras APIs ---
def get_builder_client() -> BuilderClient:
    return BuilderClient(settings.builder_url)


def get_metrics_client() -> MetricsClient:
    return MetricsClient(settings.metrics_url)


# --- servicios ---
def get_auth_service(users: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(users)


def get_blog_service(blogs: BlogRepository = Depends(get_blog_repository)) -> BlogService:
    return BlogService(blogs)


def get_page_service(
    pages: PageRepository = Depends(get_page_repository),
    blogs: BlogService = Depends(get_blog_service),
) -> PageService:
    return PageService(pages, blogs)


def get_category_service(
    categories: CategoryRepository = Depends(get_category_repository),
    blogs: BlogService = Depends(get_blog_service),
) -> CategoryService:
    return CategoryService(categories, blogs)


def get_post_service(
    posts: PostRepository = Depends(get_post_repository),
    categories: CategoryRepository = Depends(get_category_repository),
    blogs: BlogService = Depends(get_blog_service),
) -> PostService:
    return PostService(posts, categories, blogs)


def get_media_service(
    media: MediaRepository = Depends(get_media_repository),
    blogs: BlogService = Depends(get_blog_service),
) -> MediaService:
    return MediaService(media, blogs)


def get_build_service(
    builds: BuildRepository = Depends(get_build_repository),
    blogs: BlogService = Depends(get_blog_service),
    pages: PageRepository = Depends(get_page_repository),
    posts: PostRepository = Depends(get_post_repository),
    categories: CategoryRepository = Depends(get_category_repository),
    builder: BuilderClient = Depends(get_builder_client),
) -> BuildService:
    return BuildService(builds, blogs, pages, posts, categories, builder)


def get_metrics_service(
    blogs: BlogService = Depends(get_blog_service),
    client: MetricsClient = Depends(get_metrics_client),
) -> MetricsService:
    return MetricsService(blogs, client)


# --- usuario autenticado ---
def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    auth: AuthService = Depends(get_auth_service),
) -> User:
    if creds is None:
        raise UnauthorizedError()
    return auth.user_from_token(creds.credentials)
