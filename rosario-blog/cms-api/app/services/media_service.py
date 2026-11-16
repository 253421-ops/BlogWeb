import uuid
from ..exceptions import NotFoundError, PayloadTooLargeError, UnsupportedMediaError
from ..models import Media, User
from ..repository.media_repository import MediaRepository
from .blog_service import BlogService

ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_BYTES = 5 * 1024 * 1024


class MediaService:
    def __init__(self, media: MediaRepository, blogs: BlogService):
        self.media = media
        self.blogs = blogs

    def list_media(self, blog_id: int, user: User) -> list[Media]:
        blog = self.blogs.get_owned(blog_id, user)
        return self.media.list_by_blog(blog.id)

    def upload(self, blog_id: int, user: User, filename: str | None, content_type: str | None,
               data: bytes) -> Media:
        blog = self.blogs.get_owned(blog_id, user)
        ext = ALLOWED.get(content_type or "")
        if ext is None:
            raise UnsupportedMediaError("Solo se permiten imágenes JPG, PNG, WEBP o GIF")
        if len(data) > MAX_BYTES:
            raise PayloadTooLargeError("La imagen supera los 5 MB")

        stored = f"{uuid.uuid4().hex}{ext}"
        self.media.save_blob(blog.id, stored, data)

        media = Media(blog_id=blog.id, filename=filename or stored, stored_name=stored,
                      url=f"/uploads/{blog.id}/{stored}", content_type=content_type, size=len(data))
        try:
            return self.media.save(media)
        except Exception:
            self.media.delete_blob(stored)
            raise

    def read(self, blog_id: int, stored_name: str) -> bytes:
        data = self.media.get_blob(blog_id, stored_name)
        if data is None:
            raise NotFoundError("Imagen no encontrada")
        return data

    def delete(self, blog_id: int, media_id: int, user: User) -> None:
        blog = self.blogs.get_owned(blog_id, user)
        media = self.media.get_in_blog(blog.id, media_id)
        if media is None:
            raise NotFoundError("Imagen no encontrada")
        self.media.delete_blob(media.stored_name)
        self.media.delete(media)
