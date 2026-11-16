from sqlalchemy import select

from ..models import Media, MediaBlob
from .base import BlogScopedRepository


class MediaRepository(BlogScopedRepository[Media]):
    model = Media

    def list_by_blog(self, blog_id: int) -> list[Media]:
        q = select(Media).where(Media.blog_id == blog_id).order_by(Media.id.desc())
        return list(self.db.scalars(q).all())

    def save_blob(self, blog_id: int, stored_name: str, data: bytes) -> None:
        self.db.merge(MediaBlob(stored_name=stored_name, blog_id=blog_id, data=data))
        self.db.commit()

    def get_blob(self, blog_id: int, stored_name: str) -> bytes | None:
        row = self.db.get(MediaBlob, stored_name)
        return row.data if row is not None and row.blog_id == blog_id else None

    def delete_blob(self, stored_name: str) -> None:
        row = self.db.get(MediaBlob, stored_name)
        if row is not None:
            self.db.delete(row)
            self.db.commit()
